// This file is auto-generated by taxi v1.0.2, DO NOT EDIT!

package com.mycompany.csvconfig;

import java.util.*;


// 全局数值配置, 全局变量表.xlsx
public class GlobalPropertyDefine
{
    public float                GoldExchangeTimeFactor1 = 0.0f;    // 金币兑换时间参数1
    public float                GoldExchangeTimeFactor2 = 0.0f;    // 金币兑换时间参数2
    public float                GoldExchangeTimeFactor3 = 0.0f;    // 金币兑换时间参数3
    public int                  GoldExchangeResource1Price = 0;    // 金币兑换资源1价格
    public int                  GoldExchangeResource2Price = 0;    // 金币兑换资源2价格
    public int                  GoldExchangeResource3Price = 0;    // 金币兑换资源3价格
    public int                  GoldExchangeResource4Price = 0;    // 金币兑换资源4价格
    public int                  FreeCompleteSeconds = 0;           // 免费立即完成时间
    public int                  CancelBuildReturnPercent = 0;      // 取消建造后返还资源比例
    public int[]                SpawnLevelLimit = null;            // 最大刷新个数显示
    public Map<String,Integer>  FirstRechargeReward = new HashMap<>(); // 首充奖励

    private static GlobalPropertyDefine instance_;
    public static GlobalPropertyDefine getInstance() { return instance_; }

    // parse fields data from text rows
    public void parseFromRows(String[][] rows)
    {
        if (rows.length < 11) {
            throw new RuntimeException(String.format("GlobalPropertyDefine: row length out of index, %d < 11", rows.length));
        }
        if (!rows[0][3].isEmpty()) {
            this.GoldExchangeTimeFactor1 = Float.parseFloat(rows[0][3]);
        }
        if (!rows[1][3].isEmpty()) {
            this.GoldExchangeTimeFactor2 = Float.parseFloat(rows[1][3]);
        }
        if (!rows[2][3].isEmpty()) {
            this.GoldExchangeTimeFactor3 = Float.parseFloat(rows[2][3]);
        }
        if (!rows[3][3].isEmpty()) {
            this.GoldExchangeResource1Price = Integer.parseInt(rows[3][3]);
        }
        if (!rows[4][3].isEmpty()) {
            this.GoldExchangeResource2Price = Integer.parseInt(rows[4][3]);
        }
        if (!rows[5][3].isEmpty()) {
            this.GoldExchangeResource3Price = Integer.parseInt(rows[5][3]);
        }
        if (!rows[6][3].isEmpty()) {
            this.GoldExchangeResource4Price = Integer.parseInt(rows[6][3]);
        }
        if (!rows[7][3].isEmpty()) {
            this.FreeCompleteSeconds = Integer.parseInt(rows[7][3]);
        }
        if (!rows[8][3].isEmpty()) {
            this.CancelBuildReturnPercent = Integer.parseInt(rows[8][3]);
        }
        {
            String[] tokens = rows[9][3].split("\\|");
            int[] list = new int[tokens.length];
            for (int i = 0; i < tokens.length; i++) {
                if (!tokens[i].isEmpty()) {
                    int value = Integer.parseInt(tokens[i]);
                    list[i] = value;
                }
            }
            this.SpawnLevelLimit = list;
        }
        {
            String[] tokens = rows[10][3].split("\\|");
            for(int i = 0; i < tokens.length; i++) {
                String text = tokens[i];
                if (text.isEmpty()) {
                    continue;
                }
                String[] item = text.split("\\=");
                String key = item[0].trim();
                int value = Integer.parseInt(item[1]);
                this.FirstRechargeReward.put(key, value);
            }
        }
    }

    public static void loadFromFile(String filepath)
    {
        String[] lines = AutogenConfigManager.readFileToTextLines(filepath);
        String[][] rows = new String[lines.length][];
        for(int i = 0; i < lines.length; i++)
        {
            String line = lines[i];
            rows[i] = line.split("\\,", -1);
        }
        instance_ = new GlobalPropertyDefine();
        instance_.parseFromRows(rows);
    }

}
