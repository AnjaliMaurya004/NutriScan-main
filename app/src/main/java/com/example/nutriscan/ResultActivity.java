package com.example.nutriscan;

import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.cardview.widget.CardView;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.nutriscan.adapters.IngredientAdapter;
import com.example.nutriscan.models.AnalysisResult;
import com.google.gson.Gson;

public class ResultActivity extends AppCompatActivity {

    private Toolbar toolbar;
    private CardView scoreCard;
    private TextView tvScore, tvScoreLabel, tvProductName, tvRecommendation;
    private TextView tvTotalIngredients, tvMatchedCount, tvUnmatchedCount;
    private LinearLayout flagsLayout;
    private TextView tvHarmfulFlag, tvCautionFlag;
    private RecyclerView rvIngredients;

    private AnalysisResult result;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_result);

        // Get result from intent
        String jsonResult = getIntent().getStringExtra("ANALYSIS_RESULT");
        if (jsonResult != null) {
            result = new Gson().fromJson(jsonResult, AnalysisResult.class);
        }

        initViews();
        setupToolbar();

        if (result != null && result.getError() == null) {
            displayResults();
        } else {
            showError();
        }
    }

    private void initViews() {
        toolbar = findViewById(R.id.toolbar);
        scoreCard = findViewById(R.id.scoreCard);
        tvScore = findViewById(R.id.tvScore);
        tvScoreLabel = findViewById(R.id.tvScoreLabel);
        tvProductName = findViewById(R.id.tvProductName);
        tvRecommendation = findViewById(R.id.tvRecommendation);
        tvTotalIngredients = findViewById(R.id.tvTotalIngredients);
        tvMatchedCount = findViewById(R.id.tvMatchedCount);
        tvUnmatchedCount = findViewById(R.id.tvUnmatchedCount);
        flagsLayout = findViewById(R.id.flagsLayout);
        tvHarmfulFlag = findViewById(R.id.tvHarmfulFlag);
        tvCautionFlag = findViewById(R.id.tvCautionFlag);
        rvIngredients = findViewById(R.id.rvIngredients);
    }

    private void setupToolbar() {
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle("Analysis Results");
        }
        toolbar.setNavigationOnClickListener(v -> finish());
    }

    private void displayResults() {
        // Product Name
        tvProductName.setText(result.getProductName());

        // Score with color coding
        double score = result.getFinalScore();
        tvScore.setText(String.format("%.1f", score));
        tvScoreLabel.setText("/ 10");

        // Color code based on score
        int scoreColor;
        int cardColor;

        if (score >= 8) {
            scoreColor = Color.parseColor("#4CAF50"); // Green
            cardColor = Color.parseColor("#E8F5E9"); // Light Green
        } else if (score >= 6) {
            scoreColor = Color.parseColor("#8BC34A"); // Light Green
            cardColor = Color.parseColor("#F1F8E9"); // Very Light Green
        } else if (score >= 4) {
            scoreColor = Color.parseColor("#FF9800"); // Orange
            cardColor = Color.parseColor("#FFF3E0"); // Light Orange
        } else if (score >= 2) {
            scoreColor = Color.parseColor("#FF5722"); // Deep Orange
            cardColor = Color.parseColor("#FFEBEE"); // Light Red
        } else {
            scoreColor = Color.parseColor("#F44336"); // Red
            cardColor = Color.parseColor("#FFCDD2"); // Very Light Red
        }

        scoreCard.setCardBackgroundColor(cardColor);
        tvScore.setTextColor(scoreColor);
        tvScoreLabel.setTextColor(scoreColor);

        // Statistics
        tvTotalIngredients.setText(String.valueOf(result.getTotalIngredients()));
        tvMatchedCount.setText(String.valueOf(result.getMatchedIngredients()));
        tvUnmatchedCount.setText(String.valueOf(result.getUnmatchedIngredients()));

        // Recommendation
        tvRecommendation.setText(result.getRecommendation());

        // Flags
        if (result.getFlags() != null) {
            boolean hasHarmful = result.getFlags().isHasHarmful();
            boolean hasCaution = result.getFlags().isHasCaution();

            if (hasHarmful || hasCaution) {
                flagsLayout.setVisibility(View.VISIBLE);

                if (hasHarmful) {
                    tvHarmfulFlag.setVisibility(View.VISIBLE);
                }

                if (hasCaution) {
                    tvCautionFlag.setVisibility(View.VISIBLE);
                }
            } else {
                flagsLayout.setVisibility(View.GONE);
            }
        }

        // Ingredients List
        if (result.getIngredients() != null && !result.getIngredients().isEmpty()) {
            IngredientAdapter adapter = new IngredientAdapter(result.getIngredients());
            rvIngredients.setLayoutManager(new LinearLayoutManager(this));
            rvIngredients.setAdapter(adapter);
        }
    }

    private void showError() {
        tvProductName.setText("Analysis Failed");
        tvRecommendation.setText(result != null && result.getError() != null
                ? result.getError()
                : "Unable to an" +
                "alyze the product");
        scoreCard.setVisibility(View.GONE);
        rvIngredients.setVisibility(View.GONE);
    }
}