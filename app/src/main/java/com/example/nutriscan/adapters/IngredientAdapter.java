package com.example.nutriscan.adapters;

import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.cardview.widget.CardView;
import androidx.recyclerview.widget.RecyclerView;

import com.example.nutriscan.R;
import com.example.nutriscan.models.AnalysisResult;

import java.util.List;
import java.util.Locale;

public class IngredientAdapter extends RecyclerView.Adapter<IngredientAdapter.ViewHolder> {

    private List<AnalysisResult.Ingredient> ingredients;

    public IngredientAdapter(List<AnalysisResult.Ingredient> ingredients) {
        this.ingredients = ingredients;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_ingredient, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        AnalysisResult.Ingredient ingredient = ingredients.get(position);

        // Ingredient name and number
        holder.tvNumber.setText(String.valueOf(position + 1));
        holder.tvIngredientName.setText(ingredient.getName());

        // Matched as
        if (!ingredient.getMatchedAs().equals("Not in Database")) {
            holder.tvMatchedAs.setText("Matched: " + ingredient.getMatchedAs());
            holder.tvMatchedAs.setVisibility(View.VISIBLE);
        } else {
            holder.tvMatchedAs.setVisibility(View.GONE);
        }

        // Category
        if (ingredient.getCategory() != null && !ingredient.getCategory().isEmpty()) {
            holder.tvCategory.setText(ingredient.getCategory());
            holder.tvCategory.setVisibility(View.VISIBLE);
        } else {
            holder.tvCategory.setVisibility(View.GONE);
        }

        // Score and Label
        holder.tvScore.setText(String.format(Locale.getDefault(), "%.1f/10", ingredient.getScore()));
        holder.tvLabel.setText(ingredient.getLabel());

        // Confidence
        if (ingredient.getConfidence() > 0) {
            holder.tvConfidence.setText(String.format(Locale.getDefault(),
                    "Confidence: %.0f%%", ingredient.getConfidence() * 100));
            holder.tvConfidence.setVisibility(View.VISIBLE);
        } else {
            holder.tvConfidence.setVisibility(View.GONE);
        }

        // Remark
        holder.tvRemark.setText(ingredient.getRemark());

        // Color coding based on label
        String label = ingredient.getLabel().toLowerCase();
        int cardColor;
        int labelColor;
        String emoji;

        if (label.contains("healthy") || label.contains("excellent")) {
            cardColor = Color.parseColor("#E8F5E9"); // Light Green
            labelColor = Color.parseColor("#4CAF50"); // Green
            emoji = "✅";
        } else if (label.contains("caution") || label.contains("moderate")) {
            cardColor = Color.parseColor("#FFF3E0"); // Light Orange
            labelColor = Color.parseColor("#FF9800"); // Orange
            emoji = "⚠️";
        } else if (label.contains("avoid") || label.contains("harmful")) {
            cardColor = Color.parseColor("#FFEBEE"); // Light Red
            labelColor = Color.parseColor("#F44336"); // Red
            emoji = "❌";
        } else {
            cardColor = Color.parseColor("#F5F5F5"); // Light Gray
            labelColor = Color.parseColor("#757575"); // Gray
            emoji = "❓";
        }

        holder.cardView.setCardBackgroundColor(cardColor);
        holder.tvLabel.setTextColor(labelColor);
        holder. tvEmoji.setText(emoji);
    }

    @Override
    public int getItemCount() {
        return ingredients.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        CardView cardView;
        TextView tvNumber, tvEmoji, tvIngredientName, tvMatchedAs, tvCategory;
        TextView tvScore, tvLabel, tvConfidence, tvRemark;

        ViewHolder(View itemView) {
            super(itemView);
            cardView = itemView.findViewById(R.id.cardView);
            tvNumber = itemView.findViewById(R.id.tvNumber);
            tvEmoji = itemView.findViewById(R.id.tvEmoji);
            tvIngredientName = itemView.findViewById(R.id.tvIngredientName);
            tvMatchedAs = itemView.findViewById(R.id.tvMatchedAs);
            tvCategory = itemView.findViewById(R.id.tvCategory);
            tvScore = itemView.findViewById(R.id.tvScore);
            tvLabel = itemView.findViewById(R.id.tvLabel);
            tvConfidence = itemView.findViewById(R.id.tvConfidence);
            tvRemark = itemView.findViewById(R.id.tvRemark);
        }
    }
}