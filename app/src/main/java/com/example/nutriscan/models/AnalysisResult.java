package com.example.nutriscan.models;

import com.google.gson.annotations.SerializedName;
import java.util.List;

public class AnalysisResult {

    @SerializedName("product_name")
    private String productName;

    @SerializedName("final_score")
    private double finalScore;

    @SerializedName("total_ingredients")
    private int totalIngredients;

    @SerializedName("matched_ingredients")
    private int matchedIngredients;

    @SerializedName("unmatched_ingredients")
    private int unmatchedIngredients;

    @SerializedName("recommendation")
    private String recommendation;

    @SerializedName("ingredients")
    private List<Ingredient> ingredients;

    @SerializedName("flags")
    private Flags flags;

    @SerializedName("error")
    private String error;

    // Nested Ingredient class
    public static class Ingredient {
        @SerializedName("ingredient")
        private String name;

        @SerializedName("matched_as")
        private String matchedAs;

        @SerializedName("score")
        private double score;

        @SerializedName("label")
        private String label;

        @SerializedName("remark")
        private String remark;

        @SerializedName("category")
        private String category;

        @SerializedName("confidence")
        private double confidence;

        @SerializedName("method")
        private String method;

        // Getters
        public String getName() { return name; }
        public String getMatchedAs() { return matchedAs; }
        public double getScore() { return score; }
        public String getLabel() { return label; }
        public String getRemark() { return remark; }
        public String getCategory() { return category; }
        public double getConfidence() { return confidence; }
        public String getMethod() { return method; }
    }

    // Nested Flags class
    public static class Flags {
        @SerializedName("has_harmful")
        private boolean hasHarmful;

        @SerializedName("has_caution")
        private boolean hasCaution;

        // Getters
        public boolean isHasHarmful() { return hasHarmful; }
        public boolean isHasCaution() { return hasCaution; }
    }

    // Main Getters
    public String getProductName() { return productName; }
    public double getFinalScore() { return finalScore; }
    public int getTotalIngredients() { return totalIngredients; }
    public int getMatchedIngredients() { return matchedIngredients; }
    public int getUnmatchedIngredients() { return unmatchedIngredients; }
    public String getRecommendation() { return recommendation; }
    public List<Ingredient> getIngredients() { return ingredients; }
    public Flags getFlags() { return flags; }
    public String getError() { return error; }
}