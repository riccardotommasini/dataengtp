import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.sql.*;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.Random;

public class Main {
    private static final long SEED_WINDOW_SECONDS = 60;
    private static final String DB_URL = "jdbc:postgresql://db:5432/postgres";
    private static final String DB_USER = "postgres";
    private static final String DB_PASSWORD = "";

    public static void main(String[] args) throws Exception {
        Class.forName("org.postgresql.Driver");

        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/noun", handler("nouns", "ASC"));
        server.createContext("/noun-bottom", handler("nouns", "DESC"));
        server.createContext("/verb", handler("verbs"));
        server.createContext("/adjective", handler("adjectives", "ASC"));
        server.createContext("/adjective-bottom", handler("adjectives", "DESC"));
        server.start();
        System.out.println("Server started.");
    }

    private static String randomWord(String table, String order, long minuteSeed) {
        try (Connection connection = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD)) {
            try (Statement statement = connection.createStatement()) {
                try (ResultSet set = statement.executeQuery("SELECT word FROM " + table + " ORDER BY word " + order)) {
                    List<String> words = new ArrayList<>();
                    while (set.next()) {
                        words.add(set.getString(1));
                    }

                    if (!words.isEmpty()) {
                        long tableSeed = minuteSeed ^ table.hashCode() ^ order.hashCode();
                        Random random = new Random(tableSeed);
                        return words.get(random.nextInt(words.size()));
                    }
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }

        throw new NoSuchElementException(table);
    }

    private static HttpHandler handler(String table) {
        return handler(table, "ASC");
    }

    private static HttpHandler handler(String table, String order) {
        return t -> {
            long minuteSeed = Instant.now().getEpochSecond() / SEED_WINDOW_SECONDS;
            String response = "{\"word\":\"" + randomWord(table, order, minuteSeed) + "\"}";
            byte[] bytes = response.getBytes(StandardCharsets.UTF_8);

            System.out.println(response);
            t.getResponseHeaders().add("content-type", "application/json; charset=utf-8");
            t.sendResponseHeaders(200, bytes.length);

            try (OutputStream os = t.getResponseBody()) {
                os.write(bytes);
            }
        };
    }
}
