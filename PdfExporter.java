package invoiceapp;

import com.itextpdf.kernel.colors.ColorConstants;
import com.itextpdf.kernel.colors.DeviceRgb;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.borders.Border;
import com.itextpdf.layout.borders.SolidBorder;
import com.itextpdf.layout.element.Cell;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.layout.properties.UnitValue;

public class PdfExporter {

    private static final DeviceRgb HEADER_BG  = new DeviceRgb(30, 30, 80);   // dark navy
    private static final DeviceRgb ROW_ALT    = new DeviceRgb(240, 240, 250); // light lavender
    private static final DeviceRgb TOTAL_BG   = new DeviceRgb(20, 100, 60);   // dark green
    private static final DeviceRgb ACCENT     = new DeviceRgb(50, 50, 140);

    public static String export(Invoice invoice) {
        String filename = "Invoice_" + invoice.getInvoiceNumber() + ".pdf";
        try {
            PdfWriter   writer   = new PdfWriter(filename);
            PdfDocument pdfDoc   = new PdfDocument(writer);
            Document    document = new Document(pdfDoc);
            document.setMargins(36, 50, 36, 50);

            // ── Title bar ──────────────────────────────────────────────
            Paragraph title = new Paragraph("INVOICE")
                    .setFontSize(28)
                    .setBold()
                    .setFontColor(HEADER_BG)
                    .setTextAlignment(TextAlignment.CENTER);
            document.add(title);

            Paragraph subtitle = new Paragraph("Tax Invoice / GST Bill")
                    .setFontSize(11)
                    .setFontColor(ColorConstants.GRAY)
                    .setTextAlignment(TextAlignment.CENTER);
            document.add(subtitle);

            // ── Info table (invoice details + customer) ─────────────────
            Table infoTable = new Table(UnitValue.createPercentArray(new float[]{50, 50}))
                    .useAllAvailableWidth()
                    .setMarginTop(16);

            infoTable.addCell(noBorderCell("Invoice No : " + invoice.getInvoiceNumber(), false, true));
            infoTable.addCell(noBorderCell("Customer   : " + invoice.getCustomerName(), false, true));
            infoTable.addCell(noBorderCell("Date       : " + invoice.getDate(), false, false));
            infoTable.addCell(noBorderCell("Phone      : " + invoice.getCustomerPhone(), false, false));
            document.add(infoTable);

            // ── Divider ─────────────────────────────────────────────────
            document.add(new Paragraph(" ").setBorderBottom(new SolidBorder(ACCENT, 1.5f)).setMarginTop(8));

            // ── Items table ──────────────────────────────────────────────
            Table itemTable = new Table(UnitValue.createPercentArray(new float[]{40, 12, 24, 24}))
                    .useAllAvailableWidth()
                    .setMarginTop(10);

            // Header row
            for (String h : new String[]{"ITEM", "QTY", "UNIT PRICE", "TOTAL"}) {
                itemTable.addHeaderCell(
                    new Cell().add(new Paragraph(h).setBold().setFontColor(ColorConstants.WHITE))
                              .setBackgroundColor(HEADER_BG)
                              .setTextAlignment(TextAlignment.CENTER)
                              .setBorder(Border.NO_BORDER)
                              .setPadding(6)
                );
            }

            // Data rows
            boolean alt = false;
            for (Item item : invoice.getItems()) {
                DeviceRgb bg = alt ? ROW_ALT : ColorConstants.WHITE;
                itemTable.addCell(styledCell(item.getName(),                         bg, TextAlignment.LEFT));
                itemTable.addCell(styledCell(String.valueOf(item.getQuantity()),      bg, TextAlignment.CENTER));
                itemTable.addCell(styledCell(String.format("Rs. %,.2f", item.getPrice()), bg, TextAlignment.RIGHT));
                itemTable.addCell(styledCell(String.format("Rs. %,.2f", item.getTotal()), bg, TextAlignment.RIGHT));
                alt = !alt;
            }
            document.add(itemTable);

            // ── Summary table ────────────────────────────────────────────
            Table summary = new Table(UnitValue.createPercentArray(new float[]{70, 30}))
                    .useAllAvailableWidth()
                    .setMarginTop(8);

            addSummaryRow(summary, "Subtotal", invoice.getSubtotal(), false);
            if (invoice.getDiscountPercent() > 0)
                addSummaryRow(summary, "Discount (" + invoice.getDiscountPercent() + "%)",
                        invoice.getDiscountAmount(), false);
            addSummaryRow(summary, "GST (18%)", invoice.getTax(), false);

            // Grand total row
            summary.addCell(new Cell().add(new Paragraph("GRAND TOTAL").setBold()
                            .setFontColor(ColorConstants.WHITE).setFontSize(12))
                    .setBackgroundColor(TOTAL_BG).setBorder(Border.NO_BORDER)
                    .setPadding(7).setTextAlignment(TextAlignment.RIGHT));
            summary.addCell(new Cell().add(new Paragraph(String.format("Rs. %,.2f", invoice.getGrandTotal()))
                            .setBold().setFontColor(ColorConstants.WHITE).setFontSize(12))
                    .setBackgroundColor(TOTAL_BG).setBorder(Border.NO_BORDER)
                    .setPadding(7).setTextAlignment(TextAlignment.RIGHT));

            document.add(summary);

            // ── Footer ───────────────────────────────────────────────────
            document.add(new Paragraph("\nThank you for your business!")
                    .setFontSize(10).setFontColor(ColorConstants.GRAY)
                    .setTextAlignment(TextAlignment.CENTER).setMarginTop(20));

            document.close();
            return filename;

        } catch (Exception e) {
            System.out.println("❌ PDF export failed: " + e.getMessage());
            return null;
        }
    }

    // ── Helper methods ────────────────────────────────────────────────────────

    private static Cell noBorderCell(String text, boolean bold, boolean isFirst) {
        Paragraph p = new Paragraph(text).setFontSize(10);
        if (bold) p.setBold();
        return new Cell().add(p).setBorder(Border.NO_BORDER)
                .setPaddingTop(isFirst ? 4 : 1).setPaddingBottom(1);
    }

    private static Cell styledCell(String text, DeviceRgb bg, TextAlignment align) {
        return new Cell()
                .add(new Paragraph(text).setFontSize(10))
                .setBackgroundColor(bg)
                .setBorder(Border.NO_BORDER)
                .setBorderBottom(new SolidBorder(ColorConstants.LIGHT_GRAY, 0.5f))
                .setTextAlignment(align)
                .setPadding(5);
    }

    private static void addSummaryRow(Table t, String label, double value, boolean bold) {
        Paragraph lp = new Paragraph(label).setFontSize(10);
        Paragraph vp = new Paragraph(String.format("Rs. %,.2f", value)).setFontSize(10);
        if (bold) { lp.setBold(); vp.setBold(); }
        t.addCell(new Cell().add(lp).setBorder(Border.NO_BORDER)
                .setTextAlignment(TextAlignment.RIGHT).setPadding(4));
        t.addCell(new Cell().add(vp).setBorder(Border.NO_BORDER)
                .setTextAlignment(TextAlignment.RIGHT).setPadding(4));
    }
}
