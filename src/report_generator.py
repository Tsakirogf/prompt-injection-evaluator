"""
Report Generator Service

Generates PDF and Excel reports for prompt injection evaluation results.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.lib import colors


class ReportGenerator:
    """
    Service for generating evaluation reports in PDF and Excel formats.
    """
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the ReportGenerator.
        
        Args:
            output_dir: Directory where reports will be saved.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize model name for use in filename.
        
        Args:
            name: Model name to sanitize.
        
        Returns:
            Sanitized filename-safe string.
        """
        # Replace slashes and special characters
        safe_name = name.replace('/', '_').replace('\\', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ('-', '_', '.'))
        return safe_name
    
    def generate_pdf_report(
        self,
        model_name: str,
        test_results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate a PDF report for a model's test results.
        
        Args:
            model_name: Name of the model.
            test_results: List of test result dictionaries.
            metadata: Optional metadata to include in report.
        
        Returns:
            Path to the generated PDF file.
        """
        safe_name = self.sanitize_filename(model_name)
        filename = self.output_dir / f"{safe_name}.pdf"
        
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(
            f"<b>Prompt Injection Evaluation Report</b><br/>{model_name}",
            styles["Title"]
        )
        story.append(title)
        story.append(Spacer(1, 1*cm))
        
        # Metadata
        if metadata:
            story.append(Paragraph("<b>Report Information</b>", styles["Heading2"]))
            story.append(Spacer(1, 0.3*cm))
            
            for key, value in metadata.items():
                story.append(Paragraph(
                    f"<b>{key}:</b> {value}",
                    styles["Normal"]
                ))
            story.append(Spacer(1, 0.5*cm))
        
        # Summary
        if test_results:
            story.append(Paragraph("<b>Test Results Summary</b>", styles["Heading2"]))
            story.append(Spacer(1, 0.3*cm))
            
            passed = sum(1 for r in test_results if r.get('passed', False))
            failed = len(test_results) - passed
            
            story.append(Paragraph(
                f"<b>Total Tests:</b> {len(test_results)}",
                styles["Normal"]
            ))
            story.append(Paragraph(
                f"<b>Passed:</b> {passed} | <b>Failed:</b> {failed}",
                styles["Normal"]
            ))
            story.append(Spacer(1, 0.5*cm))
        
        # Detailed Results
        story.append(Paragraph("<b>Detailed Test Results</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.3*cm))
        
        for idx, result in enumerate(test_results, 1):
            story.append(Paragraph(
                f"<b>Test {idx}: {result.get('test_name', 'Unknown')}</b>",
                styles["Heading3"]
            ))
            
            story.append(Paragraph(
                f"<b>Test ID:</b> {result.get('test_id', 'N/A')}",
                styles["Normal"]
            ))
            
            story.append(Paragraph(
                f"<b>Category:</b> {result.get('category', 'N/A')}",
                styles["Normal"]
            ))
            
            story.append(Paragraph(
                f"<b>Severity:</b> {result.get('severity', 'N/A')}",
                styles["Normal"]
            ))
            
            status = "✓ PASSED" if result.get('passed', False) else "✗ FAILED"
            story.append(Paragraph(
                f"<b>Status:</b> {status}",
                styles["Normal"]
            ))
            
            if result.get('output'):
                story.append(Spacer(1, 0.2*cm))
                story.append(Paragraph("<b>Model Output:</b>", styles["Normal"]))
                output_text = str(result['output']).replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(output_text[:500], styles["Code"]))
            
            if result.get('notes'):
                story.append(Spacer(1, 0.2*cm))
                story.append(Paragraph(f"<b>Notes:</b> {result['notes']}", styles["Normal"]))
            
            story.append(Spacer(1, 0.5*cm))
            
            if idx < len(test_results):
                story.append(PageBreak())
        
        doc.build(story)
        return filename
    
    def generate_excel_report(
        self,
        model_name: str,
        test_results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate an Excel report for a model's test results.
        
        Args:
            model_name: Name of the model.
            test_results: List of test result dictionaries.
            metadata: Optional metadata to include in report.
        
        Returns:
            Path to the generated Excel file.
        """
        safe_name = self.sanitize_filename(model_name)
        filename = self.output_dir / f"{safe_name}.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Evaluation Results"
        
        # Header styling
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        # Metadata section
        row = 1
        ws.merge_cells(f'A{row}:G{row}')
        ws[f'A{row}'] = f"Prompt Injection Evaluation Report: {model_name}"
        ws[f'A{row}'].font = Font(size=16, bold=True)
        ws[f'A{row}'].alignment = Alignment(horizontal='center')
        row += 2
        
        if metadata:
            for key, value in metadata.items():
                ws[f'A{row}'] = key
                ws[f'A{row}'].font = Font(bold=True)
                ws[f'B{row}'] = value
                row += 1
            row += 1
        
        # Summary section
        if test_results:
            passed = sum(1 for r in test_results if r.get('passed', False))
            failed = len(test_results) - passed
            
            ws[f'A{row}'] = "Total Tests"
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'B{row}'] = len(test_results)
            row += 1
            
            ws[f'A{row}'] = "Passed"
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'B{row}'] = passed
            row += 1
            
            ws[f'A{row}'] = "Failed"
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'B{row}'] = failed
            row += 2
        
        # Results table headers
        headers = ['Test ID', 'Test Name', 'Category', 'Severity', 'Status', 'Output', 'Notes']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        
        row += 1
        
        # Results data
        for result in test_results:
            ws.cell(row=row, column=1, value=result.get('test_id', 'N/A'))
            ws.cell(row=row, column=2, value=result.get('test_name', 'Unknown'))
            ws.cell(row=row, column=3, value=result.get('category', 'N/A'))
            ws.cell(row=row, column=4, value=result.get('severity', 'N/A'))
            
            status = "PASSED" if result.get('passed', False) else "FAILED"
            status_cell = ws.cell(row=row, column=5, value=status)
            if status == "PASSED":
                status_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            else:
                status_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            
            ws.cell(row=row, column=6, value=str(result.get('output', ''))[:500])
            ws.cell(row=row, column=7, value=result.get('notes', ''))
            
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 50
        ws.column_dimensions['G'].width = 30
        
        wb.save(filename)
        return filename
    
    def generate_reports(
        self,
        model_name: str,
        test_results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Path]:
        """
        Generate both PDF and Excel reports.
        
        Args:
            model_name: Name of the model.
            test_results: List of test result dictionaries.
            metadata: Optional metadata to include in reports.
        
        Returns:
            Dictionary with 'pdf' and 'excel' keys containing file paths.
        """
        pdf_path = self.generate_pdf_report(model_name, test_results, metadata)
        excel_path = self.generate_excel_report(model_name, test_results, metadata)
        
        return {
            'pdf': pdf_path,
            'excel': excel_path
        }
