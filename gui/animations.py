from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint
from PySide6.QtWidgets import QGraphicsOpacityEffect

class PageAnimator:
    @staticmethod
    def animate_entry(widget):
        """
        Membuat efek widget muncul dari bawah (Slide Up) + Fade In.
        Memberikan kesan 'hidup' saat halaman dimuat.
        """
        # 1. Setup Opacity Effect (Transparansi)
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        # Animasi Opacity (0 -> 1)
        anim_opacity = QPropertyAnimation(effect, b"opacity")
        anim_opacity.setDuration(300) # 300ms
        anim_opacity.setStartValue(0)
        anim_opacity.setEndValue(1)
        anim_opacity.setEasingCurve(QEasingCurve.OutCubic)
        
        # 2. Setup Position Animation (Slide Up sedikit)
        # Kita butuh posisi asli widget dalam layout
        original_pos = widget.pos()
        start_pos = QPoint(original_pos.x(), original_pos.y() + 20) # Mulai 20px lebih bawah
        
        # Karena widget di dalam layout agak tricky dianimasikan posisinya secara absolut,
        # kita mainkan geometry atau opacity saja sudah cukup 'mahal' rasanya.
        # Tapi untuk aman di dalam QStackedWidget, Opacity saja sudah sangat 'clean'.
        # Jika ingin slide, kita mainkan geometry tapi harus hati-hati dg layout.
        
        # KITA PAKAI OPACITY SAJA + SEDIKIT SCALING (jika mungkin)
        # Untuk stabilitas layout, Fade In (Opacity) adalah yang paling aman dan elegan.
        
        anim_opacity.start()
        
        return effect # Keep reference