package com.example.nutriscan;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.ColorMatrix;
import android.graphics.ColorMatrixColorFilter;
import android.graphics.Paint;
import android.graphics.Canvas;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;

import com.example.nutriscan.api.ApiService;
import com.example.nutriscan.api.RetrofitClient;
import com.example.nutriscan.models.AnalysisResult;
import com.google.android.gms.tasks.OnFailureListener;
import com.google.android.gms.tasks.OnSuccessListener;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.Text;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

import okhttp3.MediaType;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import com.google.gson.Gson;
public class OcrActivity extends AppCompatActivity {

    private static final int CAMERA_REQUEST = 100;
    private static final int GALLERY_REQUEST = 101;
    private static final int PERMISSION_REQUEST = 200;

    private ImageView imageView;
    private Button btnCamera, btnGallery, btnAnalyze;
    private ProgressBar progressBar;
    private TextView scoreView, recommendationView, extractedTextView;
    private CardView resultCard;
    private ScrollView textScroll;

    private Bitmap selectedBitmap;
    private ApiService apiService;
    private Uri photoUri;
    private String currentPhotoPath;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_ocr);

        imageView = findViewById(R.id.imageView);
        btnCamera = findViewById(R.id.btnCamera);
        btnGallery = findViewById(R.id.btnGallery);
        btnAnalyze = findViewById(R.id.btnAnalyze);
        progressBar = findViewById(R.id.progressBar);
        scoreView = findViewById(R.id.scoreView);
        recommendationView = findViewById(R.id.recommendationView);
        extractedTextView = findViewById(R.id.extractedTextView); // ADD in XML
        resultCard = findViewById(R.id.resultCard);
        textScroll = findViewById(R.id.textScroll); // Wrap extracted text for scrolling

        apiService = RetrofitClient.getRetrofitInstance().create(ApiService.class);

        btnCamera.setOnClickListener(v -> openCamera());
        btnGallery.setOnClickListener(v -> openGallery());
        btnAnalyze.setOnClickListener(v -> {
            if (selectedBitmap != null) {
                recognizeText(selectedBitmap);
            } else {
                Toast.makeText(this, "Please select an image first", Toast.LENGTH_SHORT).show();
            }
        });
    }

    // -----------------------
    // CAMERA & GALLERY SETUP
    // -----------------------
    private void openCamera() {
        if (checkPermission()) {
            Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            File photoFile = createImageFile();
            if (photoFile != null) {
                photoUri = FileProvider.getUriForFile(this, getPackageName() + ".provider", photoFile);
                intent.putExtra(MediaStore.EXTRA_OUTPUT, photoUri);
                startActivityForResult(intent, CAMERA_REQUEST);
            }
        }
    }

    private void openGallery() {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        startActivityForResult(intent, GALLERY_REQUEST);
    }

    private boolean checkPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CAMERA}, PERMISSION_REQUEST);
            return false;
        }
        return true;
    }

    private File createImageFile() {
        File storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
        File image = new File(storageDir, "IMG_" + timeStamp + ".jpg");
        currentPhotoPath = image.getAbsolutePath();
        return image;
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (resultCode == Activity.RESULT_OK) {
            if (requestCode == CAMERA_REQUEST) {
                selectedBitmap = BitmapFactory.decodeFile(currentPhotoPath);
                imageView.setImageBitmap(selectedBitmap);
                btnAnalyze.setVisibility(View.VISIBLE);
            } else if (requestCode == GALLERY_REQUEST && data != null) {
                Uri imageUri = data.getData();
                try {
                    selectedBitmap = MediaStore.Images.Media.getBitmap(this.getContentResolver(), imageUri);
                    imageView.setImageBitmap(selectedBitmap);
                    btnAnalyze.setVisibility(View.VISIBLE);
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    // -----------------------
    // TEXT RECOGNITION
    // -----------------------
    private void recognizeText(Bitmap bitmap) {
        progressBar.setVisibility(View.VISIBLE);
        btnAnalyze.setEnabled(false);
        resultCard.setVisibility(View.GONE);
        extractedTextView.setText("");

        Bitmap processedBitmap = enhanceImage(bitmap);
        InputImage image = InputImage.fromBitmap(processedBitmap, 0);

        com.google.mlkit.vision.text.TextRecognizer recognizer =
                TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);

        recognizer.process(image)
                .addOnSuccessListener(new OnSuccessListener<Text>() {
                    @Override
                    public void onSuccess(Text visionText) {
                        progressBar.setVisibility(View.GONE);
                        btnAnalyze.setEnabled(true);

                        String recognizedText = visionText.getText();
                        if (recognizedText.isEmpty()) {
                            Toast.makeText(OcrActivity.this, "No text found!", Toast.LENGTH_SHORT).show();
                        } else {
                            extractedTextView.setText(recognizedText);
                            textScroll.setVisibility(View.VISIBLE);

                            String cleanedText = cleanIngredientsText(recognizedText);
                            sendTextToServer(cleanedText, recognizedText);
                        }
                    }
                })
                .addOnFailureListener(new OnFailureListener() {
                    @Override
                    public void onFailure(Exception e) {
                        progressBar.setVisibility(View.GONE);
                        btnAnalyze.setEnabled(true);
                        Toast.makeText(OcrActivity.this, "OCR failed: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                    }
                });
    }

    // -----------------------
    // IMAGE ENHANCEMENT
    // -----------------------
    private Bitmap enhanceImage(Bitmap original) {
        Bitmap grayscale = Bitmap.createBitmap(original.getWidth(), original.getHeight(), Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(grayscale);
        ColorMatrix cm = new ColorMatrix();
        cm.setSaturation(0); // grayscale
        Paint paint = new Paint();
        paint.setColorFilter(new ColorMatrixColorFilter(cm));
        canvas.drawBitmap(original, 0, 0, paint);

        // Increase contrast slightly
        ColorMatrix contrast = new ColorMatrix(new float[]{
                1.5f, 0, 0, 0, -30,
                0, 1.5f, 0, 0, -30,
                0, 0, 1.5f, 0, -30,
                0, 0, 0, 1, 0
        });
        paint.setColorFilter(new ColorMatrixColorFilter(contrast));
        canvas.drawBitmap(grayscale, 0, 0, paint);

        return grayscale;
    }

    // -----------------------
    // CLEAN TEXT
    // -----------------------
    private String cleanIngredientsText(String text) {
        text = text.toUpperCase();
        text = text.replaceAll("(?i)INGREDIENTS:", "");
        text = text.replaceAll("(?i)CONTAINS:.*", "");
        text = text.replaceAll("(?i)MAY CONTAIN.*", "");
        text = text.replaceAll("[^A-Z, ]", "");
        return text.trim();
    }

    // -----------------------
    // SEND TO FLASK API
    // -----------------------
    // In OcrActivity.java

    private void sendTextToServer(String text, String extractedText) {
        try {
            JSONObject json = new JSONObject();
            json.put("ingredients", text);
            json.put("product_name", "Scanned Product");

            RequestBody body = RequestBody.create(
                    MediaType.parse("application/json"), json.toString());

            Call<AnalysisResult> call = apiService.analyzeIngredients(body);
            call.enqueue(new Callback<AnalysisResult>() {
                @Override
                public void onResponse(Call<AnalysisResult> call, Response<AnalysisResult> response) {
                    progressBar.setVisibility(View.GONE);
                    btnAnalyze.setEnabled(true);

                    if (response.isSuccessful() && response.body() != null) {
                        // Open ResultActivity with the result
                        openResultActivity(response.body());
                    } else {
                        Toast.makeText(OcrActivity.this, "Analysis failed", Toast.LENGTH_SHORT).show();
                    }
                }

                @Override
                public void onFailure(Call<AnalysisResult> call, Throwable t) {
                    progressBar.setVisibility(View.GONE);
                    btnAnalyze.setEnabled(true);
                    Toast.makeText(OcrActivity.this, "Error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });

        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    // New method to open ResultActivity
    private void openResultActivity(AnalysisResult result) {
        Intent intent = new Intent(OcrActivity.this, ResultActivity.class);

        // Convert result to JSON string
        Gson gson = new Gson();
        String jsonResult = gson.toJson(result);

        intent.putExtra("ANALYSIS_RESULT", jsonResult);
        startActivity(intent);
    }}

