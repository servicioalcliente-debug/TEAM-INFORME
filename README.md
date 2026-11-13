# 📊 Dashboard de Seguimiento Académico y Certificaciones - Moodle Alianza Team

Dashboard analítico e interactivo desarrollado para monitorear en tiempo real a los estudiantes, cursos matriculados, porcentaje de avance de actividades y estado de certificación en la plataforma Moodle de **Alianza Team** ([cursosatcal.com/team](https://www.cursosatcal.com/team)).

---

## 🚀 Características Principales

* **Buscador en Tiempo Real:** Filtra instantáneamente por nombre de estudiante, correo electrónico o nombre de curso.
* **Filtros Avanzados:**
  * Selector por curso individual.
  * Selector por estado de certificación (`✅ Sí (Certificado)` / `⏳ No (Pendiente)`).
  * Selector por avance (`100% Finalizado`, `En Progreso`, `Sin Iniciar`).
  * Selector por año lectivo (`2025` y `2026`).
* **Columnas de Certificación:**
  * Indicador de aprobación/certificación.
  * Fecha y hora exacta de expedición/finalización.
* **Detalle por Actividades:** Modal interactivo para visualizar el desglose de cada video, cuestionario o evaluación completada o pendiente por estudiante.
* **Métricas y Gráficos:** Implementado con Chart.js para comparativa de inscritos vs certificados y distribución de progreso.
* **Exportador CSV:** Descarga la base de datos completa lista para Excel con un solo clic.

---

## 🌐 Publicación en GitHub Pages

Para ver el dashboard online y compartirlo sin necesidad de instalar nada:
1. Sube este repositorio a tu cuenta de GitHub.
2. Ve a **Settings** > **Pages** en tu repositorio.
3. En **Source**, selecciona `Deploy from a branch`, elige la rama `main` (o `master`) y la carpeta `/ (root)`.
4. Haz clic en **Save**. ¡Tu dashboard estará publicado en pocos minutos!

---

## 🛠️ Estructura del Proyecto

* `index.html` / `dashboard_estudiantes.html`: Dashboard autocontenido con Tailwind CSS y Chart.js.
* `moodle_progress_clean.json`: Base de datos depurada de estudiantes y cursos.
* `.gitignore`: Configurado para proteger scripts y credenciales de acceso.
