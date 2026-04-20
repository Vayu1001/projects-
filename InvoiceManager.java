package invoiceapp;

import java.util.ArrayList;
import java.util.List;

public class InvoiceManager {

    private List<Invoice> invoices;
    private final DataStore dataStore = new DataStore();

    public InvoiceManager() {
        // Load previously saved invoices from disk on startup
        invoices = dataStore.loadAll();
        if (!invoices.isEmpty())
            System.out.println("✅ Loaded " + invoices.size() + " saved invoice(s) from previous sessions.");
    }

    public void addInvoice(Invoice invoice) {
        invoices.add(invoice);
        dataStore.saveAll(invoices); // auto-save every time a new invoice is added
    }

    public List<Invoice> getAllInvoices() { return invoices; }

    public Invoice findByNumber(String invoiceNumber) {
        for (Invoice inv : invoices)
            if (inv.getInvoiceNumber().equalsIgnoreCase(invoiceNumber))
                return inv;
        return null;
    }

    /** Returns the next invoice number like INV001, INV002 … */
    public String nextInvoiceNumber() {
        return String.format("INV%03d", invoices.size() + 1);
    }
}
