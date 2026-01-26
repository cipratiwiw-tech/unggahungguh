from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtWidgets import QWidget, QStackedWidget

class PageAnimator:
    @staticmethod
    def slide_in_from_left(target_widget: QWidget, stack: QStackedWidget):
        """
        Menganimasikan widget masuk dari kiri layar ke posisi normalnya di dalam stack.
        """
        # 1. Persiapan Widget Target
        # Kita harus memastikan widget ditambahkan ke stack jika belum ada
        if stack.indexOf(target_widget) == -1:
            stack.addWidget(target_widget)
            
        # Pastikan dia terlihat dan berada di tumpukan paling atas (z-order)
        # agar menutupi widget lama saat meluncur.
        target_widget.show()
        target_widget.raise_()
        
        # 2. Hitung Geometri (Posisi & Ukuran)
        # Area tujuan adalah area total dari QStackedWidget itu sendiri
        final_rect = stack.rect()
        
        # Area awal adalah di sebelah kiri luar area tujuan (digeser sejauh lebarnya)
        start_rect = QRect(
            final_rect.x() - final_rect.width(),  # X digeser ke kiri
            final_rect.y(),                       # Y tetap
            final_rect.width(),                   # Lebar tetap
            final_rect.height()                   # Tinggi tetap
        )
        
        # 3. Set Posisi Awal Secara Paksa
        # Kita paksa widget berada di posisi start sebelum animasi dimulai.
        target_widget.setGeometry(start_rect)
        
        # 4. Setup Animasi Geometri
        anim = QPropertyAnimation(target_widget, b"geometry")
        anim.setDuration(350)  # Durasi dalam milidetik (sedikit lebih cepat agar responsif)
        # Gunakan kurva OutQuart atau OutCubic untuk efek "meluncur cepat lalu mengerem"
        anim.setEasingCurve(QEasingCurve.OutQuart) 
        anim.setStartValue(start_rect)
        anim.setEndValue(final_rect)
        
        # 5. Cleanup setelah selesai
        # Sangat penting: Beritahu stack widget bahwa widget ini sekarang adalah yang aktif.
        # Ini memastikan jika jendela di-resize nanti, layoutnya tetap benar.
        def on_finished():
            stack.setCurrentWidget(target_widget)
            # Jika widget punya fungsi refresh khusus (seperti ChannelPage), panggil di sini
            if hasattr(target_widget, 'check_auth_status'):
                target_widget.check_auth_status()
                
        anim.finished.connect(on_finished)
        
        # Simpan referensi animasi pada widget agar tidak dihapus Garbage Collector
        target_widget._slide_anim_ref = anim 
        anim.start()

    # (Fungsi animate_entry yang lama bisa dihapus jika tidak dipakai lagi di tempat lain)