package invoiceapp;

import java.time.LocalDate;
import java.util.List;
import java.util.Scanner;

public class Main {

    static Scanner        sc      = new Scanner(System.in);
    static InvoiceManager manager = new InvoiceManager();

    public static void main(String[] args) {
        printBanner();

        while (true) {
            printMenu();
            int choice = readInt("Choose option: ");
            sc.nextLine();

            switch (choice) {
                case 1 -> createInvoice();
                case 2 -> viewAllInvoices();
                case 3 -> searchInvoice();
                case 4 -> exportInvoiceToPdf();
                case 5 -> { System.out.println("\n  Goodbye! 👋\n"); return; }
                default -> System.out.println("  ⚠️  Invalid option, try again.");
            }
        }
    }

    // ── 1. Create Invoice ────────────────────────────────────────────────────
    static void createInvoice() {
        System.out.println("\n  ─── New Invoice ───────────────────────────────");
        System.out.print("  Customer Name  : ");
        String name  = sc.nextLine().trim();
        System.out.print("  Customer Phone : ");
        String phone = sc.nextLine().trim();

        String date      = LocalDate.now().toString();
        String invoiceNo = manager.nextInvoiceNumber();

        Invoice invoice = new Invoice(invoiceNo, name, phone, date);

        // Discount
        System.out.print("  Discount % (0 for none): ");
        double discount = readDouble("");
        sc.nextLine();
        invoice.setDiscountPercent(discount);

        // Add items
        System.out.println("\n  ─── Add Items (type 'done' to finish) ─────────");
        while (true) {
            System.out.print("  Item Name (or 'done'): ");
            String itemName = sc.nextLine().trim();
            if (itemName.equalsIgnoreCase("done")) break;
            if (itemName.isEmpty()) continue;

            System.out.print("  Quantity             : ");
            int qty = readInt("");
            sc.nextLine();

            System.out.print("  Price (Rs.)          : ");
            double price = readDouble("");
            sc.nextLine();

            invoice.addItem(new Item(itemName, qty, price));
            System.out.println("  ✅ Item added!\n");
        }

        if (invoice.getItems().isEmpty()) {
            System.out.println("  ⚠️  No items added. Invoice cancelled.");
            return;
        }

        System.out.println(invoice.generateInvoice());
        manager.addInvoice(invoice);
        System.out.println("  ✅ Invoice " + invoiceNo + " saved permanently!\n");

        // Offer PDF export
        System.out.print("  Export this invoice to PDF? (yes/no): ");
        if (sc.nextLine().trim().equalsIgnoreCase("yes")) {
            String file = PdfExporter.export(invoice);
            if (file != null) System.out.println("  📄 PDF saved: " + file);
        }
    }

    // ── 2. View All Invoices ─────────────────────────────────────────────────
    static void viewAllInvoices() {
        List<Invoice> list = manager.getAllInvoices();
        if (list.isEmpty()) {
            System.out.println("\n  No invoices found.\n");
            return;
        }
        System.out.println("\n  ─── All Saved Invoices ────────────────────────");
        System.out.printf("  %-10s  %-20s  %-12s  %s%n",
                "Invoice#", "Customer", "Date", "Grand Total");
        System.out.println("  " + "─".repeat(58));
        for (Invoice inv : list) {
            System.out.printf("  %-10s  %-20s  %-12s  Rs. %,.2f%n",
                    inv.getInvoiceNumber(),
                    inv.getCustomerName(),
                    inv.getDate(),
                    inv.getGrandTotal());
        }
        System.out.println();
    }

    // ── 3. Search & View Invoice ─────────────────────────────────────────────
    static void searchInvoice() {
        System.out.print("\n  Enter Invoice Number (e.g. INV001): ");
        String num = sc.nextLine().trim();
        Invoice inv = manager.findByNumber(num);
        if (inv == null) {
            System.out.println("  ❌ Invoice not found.\n");
            return;
        }
        System.out.println(inv.generateInvoice());

        System.out.print("  Export this invoice to PDF? (yes/no): ");
        if (sc.nextLine().trim().equalsIgnoreCase("yes")) {
            String file = PdfExporter.export(inv);
            if (file != null) System.out.println("  📄 PDF saved: " + file);
        }
    }

    // ── 4. Export Any Invoice to PDF ─────────────────────────────────────────
    static void exportInvoiceToPdf() {
        viewAllInvoices();
        if (manager.getAllInvoices().isEmpty()) return;
        System.out.print("  Enter Invoice Number to export: ");
        String num = sc.nextLine().trim();
        Invoice inv = manager.findByNumber(num);
        if (inv == null) { System.out.println("  ❌ Invoice not found.\n"); return; }
        String file = PdfExporter.export(inv);
        if (file != null) System.out.println("  📄 PDF exported: " + file + "\n");
    }

    // ── Helpers ───────────────────────────────────────────────────────────────
    static void printBanner() {
        System.out.println("""
                
                ╔══════════════════════════════════════╗
                ║        INVOICE GENERATOR v2.0        ║
                ║   Your data is saved automatically   ║
                ╚══════════════════════════════════════╝
                """);
    }

    static void printMenu() {
        System.out.println("  ┌─────────────────────────────────┐");
        System.out.println("  │  1. Create New Invoice          │");
        System.out.println("  │  2. View All Invoices           │");
        System.out.println("  │  3. Search Invoice by Number    │");
        System.out.println("  │  4. Export Invoice to PDF       │");
        System.out.println("  │  5. Exit                        │");
        System.out.println("  └─────────────────────────────────┘");
    }

    static int readInt(String prompt) {
        while (true) {
            try {
                if (!prompt.isEmpty()) System.out.print(prompt);
                return Integer.parseInt(sc.nextLine().trim());
            } catch (NumberFormatException e) {
                try {
                    if (!prompt.isEmpty()) System.out.print(prompt);
                    return sc.nextInt();
                } catch (Exception ex) {
                    System.out.print("  Please enter a valid number: ");
                }
            }
        }
    }

    static double readDouble(String prompt) {
        while (true) {
            try {
                if (!prompt.isEmpty()) System.out.print(prompt);
                return Double.parseDouble(sc.nextLine().trim());
            } catch (NumberFormatException e) {
                try {
                    return sc.nextDouble();
                } catch (Exception ex) {
                    System.out.print("  Please enter a valid number: ");
                }
            }
        }
    }
}
