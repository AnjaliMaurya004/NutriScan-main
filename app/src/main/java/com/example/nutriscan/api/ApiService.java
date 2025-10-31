package com.example.nutriscan.api;

import com.example.nutriscan.models.AnalysisResult;

import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;

public interface ApiService {

    @GET("/")
    Call<String> healthCheck();

    @POST("/analyze")
    Call<AnalysisResult> analyzeIngredients(@Body RequestBody body);
}