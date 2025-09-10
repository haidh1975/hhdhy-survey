"""
PDF Report Generation for Survey Analysis
"""
import os
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import base64
import tempfile

class SurveyPDFGenerator:
    """Generate PDF reports for survey analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=HexColor('#2E86AB')
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            textColor=HexColor('#A23B72')
        )
        
        # Subheader style
        self.subheader_style = ParagraphStyle(
            'CustomSubHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            textColor=HexColor('#F18F01')
        )
        
        # Body style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14
        )
    
    def generate_survey_analysis_report(
        self, 
        survey_data: Dict[str, Any],
        responses_data: List[Dict[str, Any]],
        analysis_results: Dict[str, Any],
        charts: List[go.Figure] = None
    ) -> bytes:
        """
        Generate comprehensive survey analysis PDF report
        
        Args:
            survey_data: Survey information
            responses_data: List of survey responses
            analysis_results: Statistical analysis results
            charts: List of plotly figures
            
        Returns:
            bytes: PDF content as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build the story (content)
        story = []
        
        # Title page
        story.extend(self._create_title_page(survey_data))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(survey_data, responses_data, analysis_results))
        story.append(PageBreak())
        
        # Survey overview
        story.extend(self._create_survey_overview(survey_data))
        story.append(PageBreak())
        
        # Response analysis
        story.extend(self._create_response_analysis(responses_data, analysis_results))
        
        # Charts section
        if charts:
            story.append(PageBreak())
            story.extend(self._create_charts_section(charts))
        
        # Statistical analysis
        if analysis_results:
            story.append(PageBreak())
            story.extend(self._create_statistical_analysis(analysis_results))
        
        # Conclusions and recommendations
        story.append(PageBreak())
        story.extend(self._create_conclusions())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_title_page(self, survey_data: Dict[str, Any]) -> List:
        """Create title page content"""
        story = []
        
        # Main title
        title = Paragraph(
            "BÁO CÁO PHÂN TÍCH KHẢO SÁT",
            self.title_style
        )
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # Survey title
        survey_title = Paragraph(
            f"<b>{survey_data.get('title', 'Khảo sát không có tiêu đề')}</b>",
            self.header_style
        )
        story.append(survey_title)
        story.append(Spacer(1, 0.3*inch))
        
        # Survey description
        if survey_data.get('description'):
            description = Paragraph(
                survey_data['description'],
                self.body_style
            )
            story.append(description)
            story.append(Spacer(1, 0.3*inch))
        
        # Report information
        report_info = [
            ['Ngày tạo khảo sát:', survey_data.get('created_at', 'N/A')[:10]],
            ['Ngày tạo báo cáo:', datetime.now().strftime('%d/%m/%Y')],
            ['Tổng số câu hỏi:', str(len(survey_data.get('questions', [])))],
            ['ID khảo sát:', survey_data.get('uuid', 'N/A')[:8] + '...']
        ]
        
        info_table = Table(report_info, colWidths=[2.5*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ]))
        
        story.append(Spacer(1, 1*inch))
        story.append(info_table)
        
        return story
    
    def _create_executive_summary(
        self, 
        survey_data: Dict[str, Any], 
        responses_data: List[Dict[str, Any]], 
        analysis_results: Dict[str, Any]
    ) -> List:
        """Create executive summary section"""
        story = []
        
        # Section header
        header = Paragraph("TÓM TẮT ĐIỀU HÀNH", self.header_style)
        story.append(header)
        story.append(Spacer(1, 0.2*inch))
        
        # Key metrics
        total_responses = len(responses_data)
        total_questions = len(survey_data.get('questions', []))
        
        summary_text = f"""
        <b>Tổng quan về khảo sát:</b><br/>
        • Tổng số phản hồi nhận được: {total_responses}<br/>
        • Tổng số câu hỏi trong khảo sát: {total_questions}<br/>
        • Tỷ lệ hoàn thành: {self._calculate_completion_rate(responses_data):.1f}%<br/>
        • Thời gian trung bình hoàn thành: {self._calculate_avg_completion_time(responses_data)} phút<br/><br/>
        
        <b>Kết quả chính:</b><br/>
        • Dữ liệu thu thập được từ {total_responses} người tham gia<br/>
        • Phân tích thống kê đã được thực hiện để xác định các xu hướng và mẫu<br/>
        • Báo cáo này cung cấp cái nhìn tổng quan về kết quả khảo sát và các khuyến nghị<br/>
        """
        
        summary_para = Paragraph(summary_text, self.body_style)
        story.append(summary_para)
        
        return story
    
    def _create_survey_overview(self, survey_data: Dict[str, Any]) -> List:
        """Create survey overview section"""
        story = []
        
        # Section header
        header = Paragraph("TỔNG QUAN KHẢO SÁT", self.header_style)
        story.append(header)
        story.append(Spacer(1, 0.2*inch))
        
        # Survey details
        details = Paragraph(f"""
        <b>Tiêu đề:</b> {survey_data.get('title', 'N/A')}<br/>
        <b>Mô tả:</b> {survey_data.get('description', 'Không có mô tả')}<br/>
        <b>Ngày tạo:</b> {survey_data.get('created_at', 'N/A')[:10]}<br/>
        <b>Số lượng câu hỏi:</b> {len(survey_data.get('questions', []))}<br/>
        """, self.body_style)
        story.append(details)
        story.append(Spacer(1, 0.2*inch))
        
        # Questions overview
        questions = survey_data.get('questions', [])
        if questions:
            subheader = Paragraph("CÁC CÂU HỎI TRONG KHẢO SÁT", self.subheader_style)
            story.append(subheader)
            
            question_data = []
            question_data.append(['STT', 'Loại câu hỏi', 'Nội dung câu hỏi', 'Bắt buộc'])
            
            for i, question in enumerate(questions[:10]):  # Show first 10 questions
                question_type = self._translate_question_type(question.get('type', 'text'))
                question_text = question.get('question_text', '')[:50] + ('...' if len(question.get('question_text', '')) > 50 else '')
                required = 'Có' if question.get('required', False) else 'Không'
                
                question_data.append([
                    str(i + 1),
                    question_type,
                    question_text,
                    required
                ])
            
            if len(questions) > 10:
                question_data.append(['...', '...', f'Và {len(questions) - 10} câu hỏi khác', '...'])
            
            question_table = Table(question_data, colWidths=[0.5*inch, 1.5*inch, 3*inch, 1*inch])
            question_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(question_table)
        
        return story
    
    def _create_response_analysis(
        self, 
        responses_data: List[Dict[str, Any]], 
        analysis_results: Dict[str, Any]
    ) -> List:
        """Create response analysis section"""
        story = []
        
        # Section header
        header = Paragraph("PHÂN TÍCH PHẢN HỒI", self.header_style)
        story.append(header)
        story.append(Spacer(1, 0.2*inch))
        
        # Response statistics
        total_responses = len(responses_data)
        
        if total_responses > 0:
            # Create response timeline
            response_dates = []
            for response in responses_data:
                submitted_at = response.get('submitted_at', '')
                if submitted_at:
                    try:
                        date = datetime.fromisoformat(submitted_at.replace('Z', '+00:00')).date()
                        response_dates.append(date)
                    except:
                        continue
            
            if response_dates:
                df_dates = pd.DataFrame({'date': response_dates})
                daily_counts = df_dates.groupby('date').size().reset_index(name='count')
                
                # Timeline table
                timeline_header = Paragraph("TIMELINE PHẢN HỒI", self.subheader_style)
                story.append(timeline_header)
                
                timeline_data = [['Ngày', 'Số phản hồi']]
                for _, row in daily_counts.tail(10).iterrows():  # Show last 10 days
                    timeline_data.append([
                        row['date'].strftime('%d/%m/%Y'),
                        str(row['count'])
                    ])
                
                timeline_table = Table(timeline_data, colWidths=[2*inch, 1.5*inch])
                timeline_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                story.append(timeline_table)
        
        return story
    
    def _create_charts_section(self, charts: List[go.Figure]) -> List:
        """Create charts section"""
        story = []
        
        # Section header
        header = Paragraph("BIỂU ĐỒ PHÂN TÍCH", self.header_style)
        story.append(header)
        story.append(Spacer(1, 0.2*inch))
        
        for i, fig in enumerate(charts):
            try:
                # Convert plotly figure to image
                img_bytes = pio.to_image(fig, format="png", width=600, height=400, scale=2)
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    tmp_file.write(img_bytes)
                    tmp_file_path = tmp_file.name
                
                # Add to story
                img = Image(tmp_file_path, width=5*inch, height=3.3*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
            except Exception as e:
                # If chart conversion fails, add placeholder text
                error_text = Paragraph(f"Biểu đồ {i+1}: Không thể tạo biểu đồ (lỗi: {str(e)})", self.body_style)
                story.append(error_text)
                story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _create_statistical_analysis(self, analysis_results: Dict[str, Any]) -> List:
        """Create statistical analysis section"""
        story = []
        
        # Section header
        header = Paragraph("PHÂN TÍCH THỐNG KÊ", self.header_style)
        story.append(header)
        story.append(Spacer(1, 0.2*inch))
        
        # Add statistical results
        if 'cronbach_alpha' in analysis_results:
            cronbach_text = f"""
            <b>Độ tin cậy Cronbach's Alpha:</b> {analysis_results['cronbach_alpha']:.3f}<br/>
            Đánh giá: {self._interpret_cronbach_alpha(analysis_results['cronbach_alpha'])}<br/><br/>
            """
            story.append(Paragraph(cronbach_text, self.body_style))
        
        if 'correlation_matrix' in analysis_results:
            corr_text = Paragraph("<b>Ma trận tương quan:</b> Đã được tính toán để xác định mối quan hệ giữa các biến.", self.body_style)
            story.append(corr_text)
            story.append(Spacer(1, 0.1*inch))
        
        if 'factor_analysis' in analysis_results:
            factor_text = Paragraph("<b>Phân tích nhân tố:</b> Đã thực hiện để giảm chiều dữ liệu và xác định các nhân tố chính.", self.body_style)
            story.append(factor_text)
            story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _create_conclusions(self) -> List:
        """Create conclusions and recommendations section"""
        story = []
        
        # Section header
        header = Paragraph("KẾT LUẬN VÀ KHUYẾN NGHỊ", self.header_style)
        story.append(header)
        story.append(Spacer(1, 0.2*inch))
        
        conclusions_text = """
        <b>Kết luận chính:</b><br/>
        • Dữ liệu khảo sát đã được thu thập và phân tích một cách toàn diện<br/>
        • Các mẫu và xu hướng đã được xác định từ phản hồi của người tham gia<br/>
        • Kết quả phân tích cung cấp cái nhìn sâu sắc về chủ đề khảo sát<br/><br/>
        
        <b>Khuyến nghị:</b><br/>
        • Tiếp tục thu thập thêm dữ liệu để tăng tính đại diện của mẫu<br/>
        • Thực hiện các nghiên cứu bổ sung để hiểu rõ hơn về các yếu tố ảnh hưởng<br/>
        • Áp dụng kết quả phân tích vào việc đưa ra quyết định và chính sách<br/>
        • Theo dõi và đánh giá tác động của các biện pháp được thực hiện<br/>
        """
        
        conclusions_para = Paragraph(conclusions_text, self.body_style)
        story.append(conclusions_para)
        
        return story
    
    def _translate_question_type(self, question_type: str) -> str:
        """Translate question type to Vietnamese"""
        translations = {
            'text': 'Văn bản',
            'paragraph': 'Đoạn văn',
            'number': 'Số',
            'multiple_choice': 'Trắc nghiệm',
            'checkbox': 'Hộp kiểm',
            'dropdown': 'Danh sách',
            'likert_scale': 'Thang đo Likert',
            'date': 'Ngày tháng',
            'email': 'Email',
            'phone': 'Số điện thoại'
        }
        return translations.get(question_type, question_type)
    
    def _calculate_completion_rate(self, responses_data: List[Dict[str, Any]]) -> float:
        """Calculate survey completion rate"""
        if not responses_data:
            return 0.0
        
        completed = sum(1 for response in responses_data if response.get('response_data'))
        return (completed / len(responses_data)) * 100
    
    def _calculate_avg_completion_time(self, responses_data: List[Dict[str, Any]]) -> str:
        """Calculate average completion time"""
        completion_times = []
        for response in responses_data:
            time = response.get('completion_time')
            if time and isinstance(time, (int, float)):
                completion_times.append(time)
        
        if completion_times:
            avg_seconds = sum(completion_times) / len(completion_times)
            return f"{avg_seconds / 60:.1f}"
        return "N/A"
    
    def _interpret_cronbach_alpha(self, alpha: float) -> str:
        """Interpret Cronbach's Alpha value"""
        if alpha >= 0.9:
            return "Rất tốt"
        elif alpha >= 0.8:
            return "Tốt"
        elif alpha >= 0.7:
            return "Chấp nhận được"
        elif alpha >= 0.6:
            return "Đáng ngờ"
        else:
            return "Kém"

# Utility functions for generating specific report types
def generate_survey_report(survey_uuid: str) -> Optional[bytes]:
    """Generate PDF report for a specific survey"""
    try:
        from utils.db_utils import get_survey_by_uuid_db, get_responses_db
        
        # Get survey data
        survey_data = get_survey_by_uuid_db(survey_uuid)
        if not survey_data:
            return None
        
        # Get responses
        responses_data = get_responses_db(survey_uuid)
        
        # Create PDF generator
        pdf_generator = SurveyPDFGenerator()
        
        # Generate report
        pdf_content = pdf_generator.generate_survey_analysis_report(
            survey_data=survey_data,
            responses_data=responses_data,
            analysis_results={}  # Add analysis results if available
        )
        
        return pdf_content
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return None