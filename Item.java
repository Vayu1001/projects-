package invoiceapp;

public class Item {
    private String name;
    private int quantity;
    private double price;

    public Item(String name, int quantity, double price) {
        this.name = name;
        this.quantity = quantity;
        this.price = price;
    }

    public String getName()      { return name; }
    public int getQuantity()     { return quantity; }
    public double getPrice()     { return price; }
    public double getTotal()     { return quantity * price; }

    @Override
    public String toString() {
        return String.format("%-22s %5d   Rs.%9.2f   Rs.%9.2f",
                name, quantity, price, getTotal());
    }
}
