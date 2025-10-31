package com.example.nutriscan.models;

public class IngredientDetail {
    private String ingredient;
    private double score;
    private String label;
    private String remark;
    private String matched_as;
    private String method;

    public String getIngredient() { return ingredient; }
    public double getScore() { return score; }
    public String getLabel() { return label; }
    public String getRemark() { return remark; }
    public String getMatchedAs() { return matched_as; }
    public String getMethod() { return method; }
}
