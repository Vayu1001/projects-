package invoiceapp;

import com.google.gson.*;
import com.google.gson.reflect.TypeToken;

import java.io.*;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

/**
 * Saves and loads all invoices from a local JSON file (invoices_data.json).
 * This means your data persists even after closing the program.
 */
public class DataStore {

    private static final String DATA_FILE = "invoices_data.json";
    private final Gson gson = new GsonBuilder().setPrettyPrinting().create();

    /** Load all saved invoices from disk. Returns empty list if file doesn't exist. */
    public List<Invoice> loadAll() {
        File file = new File(DATA_FILE);
        if (!file.exists()) return new ArrayList<>();

        try (Reader reader = new FileReader(file)) {
            Type listType = new TypeToken<List<InvoiceDto>>() {}.getType();
            List<InvoiceDto> dtos = gson.fromJson(reader, listType);
            if (dtos == null) return new ArrayList<>();

            List<Invoice> invoices = new ArrayList<>();
            for (InvoiceDto dto : dtos) {
                Invoice inv = new Invoice(dto.invoiceNumber, dto.customerName, dto.customerPhone, dto.date);
                inv.setDiscountPercent(dto.discountPercent);
                for (ItemDto id : dto.items) inv.addItem(new Item(id.name, id.quantity, id.price));
                invoices.add(inv);
            }
            return invoices;
        } catch (Exception e) {
            System.out.println("⚠️  Could not load saved data: " + e.getMessage());
            return new ArrayList<>();
        }
    }

    /** Save all invoices to disk. */
    public void saveAll(List<Invoice> invoices) {
        List<InvoiceDto> dtos = new ArrayList<>();
        for (Invoice inv : invoices) {
            InvoiceDto dto = new InvoiceDto();
            dto.invoiceNumber   = inv.getInvoiceNumber();
            dto.customerName    = inv.getCustomerName();
            dto.customerPhone   = inv.getCustomerPhone();
            dto.date            = inv.getDate();
            dto.discountPercent = inv.getDiscountPercent();
            dto.items           = new ArrayList<>();
            for (Item it : inv.getItems()) {
                ItemDto id = new ItemDto();
                id.name     = it.getName();
                id.quantity = it.getQuantity();
                id.price    = it.getPrice();
                dto.items.add(id);
            }
            dtos.add(dto);
        }
        try (Writer writer = new FileWriter(DATA_FILE)) {
            gson.toJson(dtos, writer);
        } catch (IOException e) {
            System.out.println("❌ Could not save data: " + e.getMessage());
        }
    }

    // ---- Simple DTO classes (plain data, no methods) ----
    static class InvoiceDto {
        String invoiceNumber, customerName, customerPhone, date;
        double discountPercent;
        List<ItemDto> items;
    }
    static class ItemDto {
        String name;
        int    quantity;
        double price;
    }
}
