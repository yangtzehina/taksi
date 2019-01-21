package com.mycompany.config;

import java.io.*;
import java.util.*;
import java.util.function.Function;

public class AutogenConfigManager {

    // parse text to boolean value
    public static boolean parseBool(String text) {
        if (!text.isEmpty()) {
            return text.equals("1") ||
                    text.equalsIgnoreCase("on") ||
                    text.equalsIgnoreCase("yes")  ||
                    text.equalsIgnoreCase("true");
        }
        return false;
    }

    public static String readFileContent(String filepath) {
        StringBuilder sb = new StringBuilder();
        try {
            BufferedReader reader = new BufferedReader(new FileReader(filepath));
            String line = null;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
                sb.append('\n'); // line break
            }
            reader.close();
        } catch(IOException ex) {
            System.err.println(ex.getMessage());
        }
        return sb.toString();
    }
    
    // you can use your own file reader
    public static Function<String, String> reader;
    
    public static String[] readFileToTextLines(String filename) {
        if (reader == null) {
            reader = (filepath)-> readFileContent(filepath);
        }
        String content = reader.apply(filename);
        return content.split("\n", -1);
    }    

    public static void loadAllConfig() {
        BoxProbabilityDefine.loadFromFile("boxprobabilitydefine.csv");
    }
}
