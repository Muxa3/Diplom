import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import json
import os  # для проверки пути к иконке
from OCR import extract_by_keywords, reload_config, CONFIG_PATH
from OneC import send_to_1c

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ОРТОРегистратор")
        self.root.geometry("700x500")
        self.root.minsize(650, 350)

        # иконка
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                print(f"Не удалось установить иконку: {e}")
        else:
            print("Файл иконки не найден")

        # цвета
        self.colors = {
            "bg_main": "#FCE4B8",
            "bg_frame": "#FFF5E6",
            "bg_entry": "#FFFFFF",
            "fg_text": "#3E2C1B",
            "btn_bg": "#4CAF50",
            "btn_fg": "#FFFFFF",
            "btn_active": "#45a049",
            "accent": "#FF8C00",
        }

        # фон окна
        self.root.configure(bg=self.colors["bg_main"])

        # вкладки
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # основная вкладка
        self.main_frame = tk.Frame(self.notebook, bg=self.colors["bg_frame"])
        self.notebook.add(self.main_frame, text="Основная")
        self._build_main_tab()

        # вкладка редактор конфига
        self.config_frame = tk.Frame(self.notebook, bg=self.colors["bg_frame"])
        self.notebook.add(self.config_frame, text="Настройки OCR")
        self._build_config_tab()

        # стили для вкладок
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=self.colors["bg_main"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["bg_frame"], foreground=self.colors["fg_text"], padding=[10, 2])
        style.map("TNotebook.Tab", background=[("selected", self.colors["accent"])])

        # загружаем конфиг в редактор
        self.load_config_to_editor()

    def _build_main_tab(self):
        # Верхняя панель с кнопками
        top_frame = tk.Frame(self.main_frame, bg=self.colors["bg_frame"])
        top_frame.pack(pady=5, fill=tk.X)

        # стили для кнопок
        btn_kwargs = {
            "bg": self.colors["btn_bg"],
            "fg": self.colors["btn_fg"],
            "activebackground": self.colors["btn_active"],
            "activeforeground": self.colors["btn_fg"],
            "font": ("Arial", 10, "bold"),
            "padx": 10,
            "pady": 5,
            "relief": "flat"
        }

        self.btn_select = tk.Button(top_frame, text="Выбрать изображения", command=self.select_files, **btn_kwargs)
        self.btn_select.pack(side=tk.LEFT, padx=5)

        self.btn_process = tk.Button(top_frame, text="Обработать", command=self.process_files, **btn_kwargs)
        self.btn_process.pack(side=tk.LEFT, padx=5)

        self.btn_send = tk.Button(top_frame, text="Отправить в 1С", command=self.send_data, **btn_kwargs)
        self.btn_send.pack(side=tk.LEFT, padx=5)
        self.btn_send.config(state=tk.DISABLED)

        self.lbl_status = tk.Label(
            self.main_frame,
            text="Готов",
            bg=self.colors["bg_frame"],
            fg=self.colors["fg_text"],
            font=("Arial", 10, "italic")
        )
        self.lbl_status.pack(pady=5)

        # рамка с редактируемыми полями
        fields_frame = tk.LabelFrame(
            self.main_frame,
            text="Редактируемые данные",
            padx=10,
            pady=10,
            bg=self.colors["bg_frame"],
            fg=self.colors["accent"],
            font=("Arial", 10, "bold")
        )
        fields_frame.pack(fill=tk.X, padx=10, pady=5)

        self.field_names = ['Номер направления', 'ФИО', 'СНИЛС', 'Паспорт', 'Услуга']
        self.entries = {}

        for field in self.field_names:
            row = tk.Frame(fields_frame, bg=self.colors["bg_frame"])
            row.pack(fill=tk.X, pady=2)
            lbl = tk.Label(
                row,
                text=field + ":",
                width=20,
                anchor='e',
                bg=self.colors["bg_frame"],
                fg=self.colors["fg_text"],
                font=("Arial", 10)
            )
            lbl.pack(side=tk.LEFT)
            entry = tk.Entry(
                row,
                width=50,
                bg=self.colors["bg_entry"],
                fg=self.colors["fg_text"],
                insertbackground=self.colors["accent"],
                font=("Arial", 10)
            )
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.entries[field] = entry

        # логи
        self.log_text = scrolledtext.ScrolledText(
            self.main_frame,
            height=12,
            bg=self.colors["bg_entry"],
            fg=self.colors["fg_text"],
            insertbackground=self.colors["accent"],
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_config_tab(self):
        # текстовое поле для редактирования конфига
        lbl = tk.Label(
            self.config_frame,
            text="Редактируйте параметры конфигурации (JSON):",
            bg=self.colors["bg_frame"],
            fg=self.colors["fg_text"],
            font=("Arial", 10, "bold")
        )
        lbl.pack(pady=5)

        self.config_editor = scrolledtext.ScrolledText(
            self.config_frame,
            height=20,
            width=80,
            bg=self.colors["bg_entry"],
            fg=self.colors["fg_text"],
            insertbackground=self.colors["accent"],
            font=("Consolas", 10)
        )
        self.config_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # кнопки управления
        btn_frame = tk.Frame(self.config_frame, bg=self.colors["bg_frame"])
        btn_frame.pack(pady=5)

        btn_kwargs = {
            "bg": self.colors["btn_bg"],
            "fg": self.colors["btn_fg"],
            "activebackground": self.colors["btn_active"],
            "activeforeground": self.colors["btn_fg"],
            "font": ("Arial", 10, "bold"),
            "padx": 10,
            "pady": 5,
            "relief": "flat"
        }

        btn_save = tk.Button(btn_frame, text="Сохранить", command=self.save_config, **btn_kwargs)
        btn_save.pack(side=tk.LEFT, padx=5)

        btn_reload = tk.Button(btn_frame, text="Сбросить", command=self.load_config_to_editor, **btn_kwargs)
        btn_reload.pack(side=tk.LEFT, padx=5)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def select_files(self):
        self.files = filedialog.askopenfilenames(
            title="Выберите изображения",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg")]
        )
        if self.files:
            self.log(f"Выбрано файлов: {len(self.files)}")
            for f in self.files:
                self.log(f"  {f}")
        else:
            self.log("Файлы не выбраны")

    def process_files(self):
        if not self.files:
            self.log("Сначала выберите файлы")
            return
        threading.Thread(target=self._process_thread, daemon=True).start()

    def _process_thread(self):
        self.root.after(0, lambda: self.btn_process.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.btn_send.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.lbl_status.config(text="Идёт обработка..."))
        self.log("=== Начало обработки ===")

        all_data = []
        for path in self.files:
            self.log(f"Обработка {path}...")
            try:
                data = extract_by_keywords(path, binarization=True)
                self.log(f"Извлечено: {data}")
                all_data.append(data)
            except Exception as e:
                self.log(f"Ошибка при обработке {path}: {e}")
                continue

        merged = {}
        for data in all_data:
            merged.update(data)

        self.log(f"Объединённые данные: {merged}")
        self.extracted_data = merged

        self.root.after(0, self._update_entries)

        self.log("=== Обработка завершена ===")
        self.root.after(0, lambda: self.lbl_status.config(text="Готово, можно редактировать и отправлять"))
        self.root.after(0, lambda: self.btn_process.config(state=tk.NORMAL))
        if merged:
            self.root.after(0, lambda: self.btn_send.config(state=tk.NORMAL))
        else:
            self.root.after(0, lambda: self.btn_send.config(state=tk.DISABLED))

    def _update_entries(self):
        for field, entry in self.entries.items():
            value = self.extracted_data.get(field, "")
            entry.delete(0, tk.END)
            entry.insert(0, value)

    def send_data(self):
        data = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if value:
                data[field] = value
        if not data:
            messagebox.showwarning("Нет данных", "Поля пусты. Заполните данные перед отправкой.")
            return

        threading.Thread(target=self._send_thread, args=(data,), daemon=True).start()

    def _send_thread(self, data):
        self.root.after(0, lambda: self.btn_send.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.lbl_status.config(text="Отправка в 1С..."))
        self.log(f"Отправка данных: {data}")
        try:
            send_to_1c(data)
            self.log(f"Отправлено направление {data.get('Номер направления')}")
            self.root.after(0, lambda: messagebox.showinfo("Успех", "Данные успешно отправлены в 1С"))
        except Exception as e:
            self.log(f"Ошибка отправки: {e}")
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка отправки: {e}"))
        finally:
            self.root.after(0, lambda: self.lbl_status.config(text="Готов"))
            self.root.after(0, lambda: self.btn_send.config(state=tk.NORMAL))
    # загружает конфиг (забыл да?)
    def load_config_to_editor(self):
        """Загружает содержимое config.json в текстовое поле редактора."""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config_text = f.read()
            try:
                config_json = json.loads(config_text)
                formatted = json.dumps(config_json, indent=2, ensure_ascii=False)
            except:
                formatted = config_text
            self.config_editor.delete(1.0, tk.END)
            self.config_editor.insert(1.0, formatted)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить конфиг: {e}")

    # сохраняет новый конфиг и перезагружает его параметры в OCR
    def save_config(self):
        """Сохраняет содержимое редактора в config.json и перезагружает конфиг в OCR."""
        content = self.config_editor.get(1.0, tk.END).strip()
        try:
            # Проверяем валидность JSON
            config_data = json.loads(content)
            # Сохраняем в файл
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            # Перезагружаем конфиг в OCR
            reload_config()
            messagebox.showinfo("Успех", "Конфигурация сохранена и перезагружена.")
            # Обновляем отображение (форматируем)
            formatted = json.dumps(config_data, indent=2, ensure_ascii=False)
            self.config_editor.delete(1.0, tk.END)
            self.config_editor.insert(1.0, formatted)
        except json.JSONDecodeError as e:
            messagebox.showerror("Ошибка", f"Некорректный JSON: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить конфиг: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()