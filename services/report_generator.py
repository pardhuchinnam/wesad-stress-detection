from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import io
import logging

logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """Generate PDF reports for weekly stress/emotion summary"""

    def __init__(self, user, predictions):
        """
        Args:
            user: User object
            predictions: list of prediction dicts from database
        """
        self.user = user
        self.predictions = predictions
        self.styles = getSampleStyleSheet()

    def generate_report(self, output_path='reports/weekly_report.pdf'):
        """Generate complete PDF report"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2C3E50'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            title = Paragraph(f"Weekly Wellness Report", title_style)
            story.append(title)
            story.append(Spacer(1, 0.2 * inch))

            # User info
            info_text = f"""
            <b>Name:</b> {self.user.username}<br/>
            <b>Email:</b> {self.user.email}<br/>
            <b>Report Period:</b> {(datetime.now() - timedelta(days=7)).strftime('%B %d, %Y')} 
                                to {datetime.now().strftime('%B %d, %Y')}<br/>
            <b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            """
            info_para = Paragraph(info_text, self.styles['Normal'])
            story.append(info_para)
            story.append(Spacer(1, 0.3 * inch))

            # Summary statistics
            story.append(self._create_summary_section())
            story.append(Spacer(1, 0.3 * inch))

            # Emotion distribution chart
            chart_path = self._create_emotion_chart()
            if chart_path:
                story.append(Image(chart_path, width=5 * inch, height=3 * inch))
                story.append(Spacer(1, 0.2 * inch))

            # Daily breakdown table
            story.append(self._create_daily_table())
            story.append(Spacer(1, 0.3 * inch))

            # Recommendations
            story.append(self._create_recommendations())

            # Build PDF
            doc.build(story)
            logger.info(f"Report generated: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return None

    def _create_summary_section(self):
        """Create summary statistics section"""
        # Calculate statistics
        total_readings = len(self.predictions)

        stress_count = sum(1 for p in self.predictions if p['stress_level'] == 'stress')
        baseline_count = sum(1 for p in self.predictions if p['stress_level'] == 'baseline')
        amusement_count = sum(1 for p in self.predictions if p['stress_level'] == 'amusement')

        stress_percentage = (stress_count / total_readings * 100) if total_readings > 0 else 0

        # Create table
        data = [
            ['Metric', 'Value'],
            ['Total Readings', str(total_readings)],
            ['Stress Episodes', f'{stress_count} ({stress_percentage:.1f}%)'],
            ['Baseline State', f'{baseline_count}'],
            ['Relaxed/Amusement', f'{amusement_count}'],
            ['Average Confidence', f'{np.mean([p["confidence"] for p in self.predictions]):.2f}']
        ]

        table = Table(data, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        return table

    def _create_emotion_chart(self):
        """Create emotion distribution pie chart"""
        try:
            emotions = [p['stress_level'] for p in self.predictions]
            unique, counts = np.unique(emotions, return_counts=True)

            colors_map = {
                'baseline': '#95A5A6',
                'stress': '#E74C3C',
                'amusement': '#2ECC71'
            }

            fig, ax = plt.subplots(figsize=(8, 6))
            colors_list = [colors_map.get(e, '#BDC3C7') for e in unique]

            ax.pie(counts, labels=unique, autopct='%1.1f%%', colors=colors_list, startangle=90)
            ax.set_title('Emotion Distribution', fontsize=16, fontweight='bold')

            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()

            temp_path = 'static/temp_emotion_chart.png'
            with open(temp_path, 'wb') as f:
                f.write(img_buffer.getvalue())

            return temp_path

        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            return None

    def _create_daily_table(self):
        """Create daily breakdown table"""
        # Group by day
        from collections import defaultdict
        daily_data = defaultdict(lambda: {'stress': 0, 'baseline': 0, 'amusement': 0})

        for pred in self.predictions:
            day = pred['timestamp'].split('T')[0]  # Extract date
            daily_data[day][pred['stress_level']] += 1

        # Create table
        data = [['Date', 'Stress', 'Baseline', 'Amusement', 'Total']]

        for day in sorted(daily_data.keys(), reverse=True):
            counts = daily_data[day]
            total = counts['stress'] + counts['baseline'] + counts['amusement']
            data.append([
                day,
                str(counts['stress']),
                str(counts['baseline']),
                str(counts['amusement']),
                str(total)
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        return table

    def _create_recommendations(self):
        """Create recommendations section"""
        stress_count = sum(1 for p in self.predictions if p['stress_level'] == 'stress')
        stress_ratio = stress_count / len(self.predictions) if self.predictions else 0

        if stress_ratio > 0.5:
            recommendation_text = """
            <b>⚠️ High Stress Alert:</b><br/>
            Your stress levels have been elevated this week. Consider:<br/>
            • Scheduling regular breaks during work<br/>
            • Practicing mindfulness meditation (10-15 min daily)<br/>
            • Engaging in physical exercise<br/>
            • Getting 7-8 hours of quality sleep<br/>
            • Consulting with a healthcare professional if stress persists
            """
        elif stress_ratio > 0.3:
            recommendation_text = """
            <b>✅ Moderate Stress:</b><br/>
            Your stress is manageable but can be improved:<br/>
            • Continue monitoring your stress patterns<br/>
            • Maintain work-life balance<br/>
            • Practice stress-relief techniques<br/>
            • Stay physically active
            """
        else:
            recommendation_text = """
            <b>🎉 Excellent Stress Management!</b><br/>
            Keep up the great work:<br/>
            • Continue your current wellness routine<br/>
            • Share your strategies with others<br/>
            • Stay consistent with healthy habits
            """

        return Paragraph(recommendation_text, self.styles['Normal'])


# API endpoint function
def generate_user_report(user_id):
    """Generate report for a specific user"""
    try:
        import database
        from models import User

        user = User.query.get(user_id)
        if not user:
            return None

        # Get last 7 days of predictions
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        predictions = database.get_user_predictions_since(user_id, cutoff_date)

        if not predictions:
            logger.warning(f"No predictions found for user {user_id}")
            return None

        # Generate report
        report_gen = WeeklyReportGenerator(user, predictions)
        output_path = f'reports/weekly_report_{user_id}_{datetime.now().strftime("%Y%m%d")}.pdf'

        return report_gen.generate_report(output_path)

    except Exception as e:
        logger.error(f"Report generation failed for user {user_id}: {e}")
        return None
