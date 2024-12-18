import os
import shutil
import tkinter as tk
from tkinter import messagebox, Canvas
from PIL import Image, ImageTk, UnidentifiedImageError
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ServoAngleGUI:
    def __init__(self, root, data_folder="data/images", temp_folder="data/temp", processed_folder="data/processed"):
        self.root = root
        self.root.title("Servo Angle File Manager")

        # 폴더 설정
        self.data_folder = data_folder
        self.temp_folder = temp_folder
        self.processed_folder = processed_folder
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)
        if not os.path.exists(self.processed_folder):
            os.makedirs(self.processed_folder)

        # 파일 목록과 현재 인덱스
        self.file_list = []
        self.current_index = 0

        # 각도 분포 초기화
        self.angle_distribution = {30: 0, 60: 0, 90: 0, 120: 0, 150: 0}
        self.update_file_list()
        self.update_angle_distribution()

        # GUI 구성
        self.create_widgets()

        # 키보드 이벤트 바인딩
        self.root.bind('a', self.move_left)   # 이전 사진으로 이동
        self.root.bind('d', self.move_right)  # 다음 사진으로 이동
        self.root.bind('r', self.restore_files)  # 삭제된 파일 복구
        self.root.bind('<Delete>', self.delete_current_photo)  # Delete 키로 삭제

    def create_widgets(self):
        # 캔버스: 사진 및 삭제 버튼
        self.photo_frame = tk.Frame(self.root)
        self.photo_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.photo_canvas = Canvas(self.photo_frame, width=500, height=500, bg="white")
        self.photo_canvas.pack()

        self.delete_button = tk.Button(self.photo_frame, text="Delete", command=self.delete_current_photo)
        self.delete_button.pack(side=tk.TOP, pady=5)

        # 각도 분포 그래프
        self.graph_frame = tk.Frame(self.root)
        self.graph_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.angle_graph = self.figure.add_subplot(111)
        self.graph_canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.graph_canvas.get_tk_widget().pack()

        # 파일 목록과 그래프 초기화
        self.update_graph()
        self.display_current_photo()

    def is_valid_image(self, file_path):
        """이미지가 손상되었는지 확인"""
        try:
            with Image.open(file_path) as img:
                img.verify()  # 이미지 파일 검증
            return True
        except (UnidentifiedImageError, IOError):
            return False

    def update_file_list(self):
        # 파일 목록 업데이트 및 손상된 파일 자동 삭제
        all_files = [
            file for file in os.listdir(self.data_folder)
            if file.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]
        valid_files = []
        for file in all_files:
            file_path = os.path.join(self.data_folder, file)
            if self.is_valid_image(file_path):
                valid_files.append(file)
            else:
                # 손상된 파일을 temp로 이동
                print(f"손상된 파일 삭제: {file}")
                shutil.move(file_path, os.path.join(self.temp_folder, file))

        self.file_list = valid_files
        if self.current_index >= len(self.file_list):
            self.current_index = len(self.file_list) - 1
        if len(self.file_list) == 0:
            self.current_index = 0

    def delete_current_photo(self, event=None):
        # 현재 사진 삭제
        if self.file_list:
            current_file = self.file_list[self.current_index]
            src_path = os.path.join(self.data_folder, current_file)
            dst_path = os.path.join(self.temp_folder, current_file)
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete: {current_file}?")
            if confirm:
                shutil.move(src_path, dst_path)
                messagebox.showinfo("Photo Deleted", f"Deleted: {current_file}")
                self.update_file_list()
                self.update_angle_distribution()
                self.update_graph()
                self.display_current_photo()

    def restore_files(self, event=None):
        # 삭제된 파일 복구
        for file in os.listdir(self.temp_folder):
            src_path = os.path.join(self.temp_folder, file)
            dst_path = os.path.join(self.data_folder, file)
            shutil.move(src_path, dst_path)
        messagebox.showinfo("Files Restored", "All files have been restored.")
        self.update_file_list()
        self.update_angle_distribution()
        self.update_graph()
        self.display_current_photo()

    def move_left(self, event=None):
        # 이전 사진으로 이동
        if self.file_list and self.current_index > 0:
            self.current_index -= 1
            self.display_current_photo()

    def move_right(self, event=None):
        # 다음 사진으로 이동
        if self.file_list and self.current_index < len(self.file_list) - 1:
            self.current_index += 1
            self.display_current_photo()

    def display_current_photo(self):
        # 현재 사진 표시 및 각도 시각화
        self.photo_canvas.delete("all")
        if self.file_list:
            current_file = self.file_list[self.current_index]
            file_path = os.path.join(self.data_folder, current_file)
            try:
                with Image.open(file_path) as img:
                    angle = self.extract_angle_from_filename(current_file)
                    img_resized = img.resize((500, 500), Image.LANCZOS)
                    draw = ImageTk.PhotoImage(img_resized)
                    self.photo_canvas.image = draw
                    self.photo_canvas.create_image(0, 0, anchor=tk.NW, image=draw)
                    self.photo_canvas.create_text(250, 480, text=f"Angle: {angle}°", font=("Helvetica", 12), fill="red")
            except Exception as e:
                print(f"Error displaying image: {e}")
        else:
            self.photo_canvas.create_text(250, 250, text="No photos available", font=("Helvetica", 16), fill="gray")

    def update_angle_distribution(self):
        # 각도 분포 계산
        self.angle_distribution = {30: 0, 60: 0, 90: 0, 120: 0, 150: 0}
        for file in self.file_list:
            angle = self.extract_angle_from_filename(file)
            if angle in self.angle_distribution:
                self.angle_distribution[angle] += 1

    def extract_angle_from_filename(self, filename):
        # 파일명에서 각도 추출 (예: "image_angle_90.jpg")
        try:
            if "angle_" in filename:
                angle_part = filename.split("angle_")[1].split(".")[0]
                return int(angle_part)
        except:
            return None
        return 90  # Default angle

    def update_graph(self):
        # 각도 분포 그래프 업데이트
        self.angle_graph.clear()
        angles = list(self.angle_distribution.keys())
        counts = list(self.angle_distribution.values())
        self.angle_graph.bar(angles, counts, color='blue', alpha=0.7)
        self.angle_graph.set_title("Angle Distribution")
        self.angle_graph.set_xlabel("Angles")
        self.angle_graph.set_ylabel("Count")
        self.graph_canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServoAngleGUI(root, data_folder="data/images", temp_folder="data/temp", processed_folder="data/processed")
    root.mainloop()
