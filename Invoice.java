package invoiceapp;

import java.util.ArrayList;
import java.util.List;

public class Invoice {
    private String invoiceNumber;
    private String customerName;
    private String customerPhone;
    private String date;
    private List<Item> items;
    private double taxRate = 0.18; // 18% GST
    private double discountPercent = 0.0;

    public Invoice(String invoiceNumber, String customerName, String customerPhone, String date) {
        this.invoiceNumber = invoiceNumber;
        this.customerName  = customerName;
        this.customerPhone = customerPhone;
        this.date          = date;
        this.items         = new ArrayList<>();
    }

    public void addItem(Item item)            { items.add(item); }
    public List<Item> getItems()              { return items; }
    public String getInvoiceNumber()          { return invoiceNumber; }
    public String getCustomerName()           { return customerName; }
    public String getCustomerPhone()          { return customerPhone; }
    public String getDate()                   { return date; }
    public double getDiscountPercent()        { return discountPercent; }
    public void   setDiscountPercent(double d){ this.discountPercent = d; }

    public double getSubtotal() {
        double sub = 0;
        for (Item i : items) sub += i.getTotal();
        return sub;
    }

    public double getDiscountAmount() { return getSubtotal() * (discountPercent / 100); }
    public double getAfterDiscount()  { return getSubtotal() - getDiscountAmount(); }
    public double getTax()            { return getAfterDiscount() * taxRate; }
    public double getGrandTotal()     { return getAfterDiscount() + getTax(); }

    public String generateInvoice() {
        StringBuilder sb = new StringBuilder();
        sb.append("\n===========================================================\n");
        sb.append("                    INVOICE GENERATOR                     \n");
        sb.append("===========================================================\n");
        sb.append(String.format("  Invoice No  : %s%n", invoiceNumber));
        sb.append(String.format("  Customer    : %s%n", customerName));
        sb.append(String.format("  Phone       : %s%n", customerPhone));
        sb.append(String.format("  Date        : %s%n", date));
        sb.append("-----------------------------------------------------------\n");
        sb.append(String.format("%-22s %5s   %11s   %11s%n", "Item", "Qty", "Price", "Total"));
        sb.append("-----------------------------------------------------------\n");
        for (Item item : items) sb.append(item.toString()).append("\n");
        sb.append("-----------------------------------------------------------\n");
        sb.append(String.format("%-43s Rs.%9.2f%n", "  Subtotal:", getSubtotal()));
        if (discountPercent > 0)
            sb.append(String.format("%-43s Rs.%9.2f%n",
                    "  Discount (" + discountPercent + "%):", getDiscountAmount()));
        sb.append(String.format("%-43s Rs.%9.2f%n", "  GST (18%):", getTax()));
        sb.append("===========================================================\n");
        sb.append(String.format("%-43s Rs.%9.2f%n", "  GRAND TOTAL:", getGrandTotal()));
        sb.append("===========================================================\n");
        return sb.toString();
    }
}
