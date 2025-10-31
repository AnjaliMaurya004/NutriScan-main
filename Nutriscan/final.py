import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
import json

# ===============================
# CONFIGURATION
# ===============================
SIMILARITY_THRESHOLD = 0.35
CACHE_SIZE = 500

# ===============================
# E-NUMBER MAPPING
# ===============================
E_NUMBER_MAP = {
    'e330': 'citric acid',
    'e500': 'sodium carbonate',
    'e501': 'potassium carbonate',
    'e508': 'potassium chloride',
    'e170': 'calcium carbonate',
    'e412': 'guar gum',
    'e452': 'sodium phosphate',
    'e100': 'curcumin',
    'e627': 'disodium guanylate',
    'e631': 'disodium inosinate',
    'e551': 'silicon dioxide',
    'e621': 'monosodium glutamate',
    'e322': 'lecithin',
    'e471': 'mono and diglycerides',
    'e407': 'carrageenan',
    'e410': 'locust bean gum',
    'e415': 'xanthan gum',
    'e150': 'caramel',
    'e202': 'potassium sorbate',
    'e211': 'sodium benzoate',
    'e223': 'sodium metabisulphite',
}

# ===============================
# INDIAN INGREDIENT MAPPING
# ===============================
INDIAN_INGREDIENT_MAP = {
    'maida': 'refined wheat flour',
    'atta': 'whole wheat flour',
    'besan': 'gram flour',
    'hing': 'asafoetida',
    'jeera': 'cumin',
    'haldi': 'turmeric',
    'dhaniya': 'coriander',
    'elaichi': 'cardamom',
    'dalchini': 'cinnamon',
    'kalonji': 'nigella seeds',
    'methi': 'fenugreek',
    'ajwain': 'carom seeds',
    'til': 'sesame',
    'kaju': 'cashew',
    'badam': 'almond',
    'pista': 'pistachio',
    'khoya': 'milk solids',
    'paneer': 'cottage cheese',
}

# ===============================
# LOAD DATASET & SETUP
# ===============================
class FoodAnalyzer:
    def __init__(self, csv_path="food_ingridients.csv"):
        """Initialize the food analyzer with dataset and ML models."""
        self.df = pd.read_csv(csv_path)
        self.df.fillna("", inplace=True)
        
        # Preprocess dataset
        self.df['Ingredient_LC'] = self.df['Food_Ingredient'].str.lower()
        self.ingredient_set = set(self.df['Ingredient_LC'].values)
        
        # Setup TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 3),  # Capture 1-3 word phrases
            min_df=1
        )
        self.ingredient_vectors = self.vectorizer.fit_transform(
            self.df['Food_Ingredient']
        )
        
        print("✅ Food Analyzer initialized successfully!")
        print(f"📊 Loaded {len(self.df)} ingredients from database")

    # ===============================
    # TEXT CLEANING
    # ===============================
    def clean_ingredient_text(self, raw_text):
        """Advanced OCR text preprocessing."""
        text = raw_text.lower()
        
        # Remove common packaging phrases
        removal_patterns = [
            r"allergen advice[:\s].*",
            r"may contain traces of.*",
            r"contains added permitted.*",
            r"added flavours?.*",
            r"natural identical flavouring substances?.*",
            r"ingredients?[:\s]",
            r"noodles[:\s]",
            r"tastemaker[:\s]",
            r"seasoning[:\s]",
        ]
        for pattern in removal_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Replace E-numbers with actual names
        for e_code, ingredient_name in E_NUMBER_MAP.items():
            text = re.sub(rf'\b{e_code}\b', ingredient_name, text)
        
        # Replace Indian names with English equivalents
        for indian, english in INDIAN_INGREDIENT_MAP.items():
            text = re.sub(rf'\b{indian}\b', english, text)
        
        # Remove content in brackets/parentheses
        text = re.sub(r"[\[\(].*?[\]\)]", "", text)
        
        # Remove descriptive phrases
        text = re.sub(r"\b(as|for)\s+(thickener|stabilizer|emulsifier|preservative|colour|flavor|acidity regulator|raising agent|anticaking agent)\b", "", text)
        
        # Remove variant numbers
        text = re.sub(r"\bvariant\s+\d+", "", text)
        
        # Replace separators with commas
        text = re.sub(r"[:;\n\t&/]", ",", text)
        
        # Remove numbers and special characters
        text = re.sub(r"[^a-z,\s]", "", text)
        
        # Collapse whitespace and commas
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r",+", ",", text)
        
        # Clean edges
        text = text.strip(", ")
        
        return text

    # ===============================
    # CACHING LAYER
    # ===============================
    @lru_cache(maxsize=CACHE_SIZE)
    def get_ingredient_score_cached(self, ingredient):
        """Cache ingredient lookups for performance."""
        return self._get_ingredient_score(ingredient)

    # ===============================
    # INGREDIENT SCORING
    # ===============================
    def _get_ingredient_score(self, ingredient):
        """Get score for a single ingredient using hybrid approach."""
        ing_lc = ingredient.lower().strip()
        
        # Step 1: Exact match
        if ing_lc in self.ingredient_set:
            row = self.df[self.df['Ingredient_LC'] == ing_lc].iloc[0]
            return {
                'ingredient': ingredient,
                'matched_as': row['Food_Ingredient'],
                'score': float(row['Nutrition_Score']),
                'label': row['Health_Label'],
                'remark': row['Remarks'],
                'method': 'exact_match'
            }
        
        # Step 2: TF-IDF Similarity
        input_vec = self.vectorizer.transform([ing_lc])
        sims = cosine_similarity(input_vec, self.ingredient_vectors)
        best_idx = sims.argmax()
        best_score = sims[0][best_idx]
        
        if best_score > SIMILARITY_THRESHOLD:
            row = self.df.iloc[best_idx]
            return {
                'ingredient': ingredient,
                'matched_as': row['Food_Ingredient'],
                'score': float(row['Nutrition_Score']),
                'label': row['Health_Label'],
                'remark': row['Remarks'],
                'method': f'tfidf_match ({best_score:.2f})'
            }
        
        # Step 3: Keyword-based inference
        score, label, remark = self._infer_unknown_ingredient(ing_lc)
        return {
            'ingredient': ingredient,
            'matched_as': 'Unknown',
            'score': score,
            'label': label,
            'remark': remark,
            'method': 'keyword_inference'
        }

    # ===============================
    # FALLBACK SCORING
    # ===============================
    def _infer_unknown_ingredient(self, ingredient):
        """Advanced keyword-based scoring for unknown ingredients."""
        ing = ingredient.lower()
        
        # Harmful additives
        if any(x in ing for x in ["color", "colour", "dye", "tartrazine"]):
            return (2, "Avoid", "⚠️ Artificial colorant; may cause allergic reactions.")
        
        # Preservatives
        if any(x in ing for x in ["preservative", "benzoate", "sorbate", "sulfite", "nitrite"]):
            return (3, "Caution", "⚠️ Chemical preservative; limit consumption.")
        
        # Flavor enhancers
        if any(x in ing for x in ["msg", "monosodium glutamate", "disodium", "flavor enhancer"]):
            return (3, "Caution", "⚠️ Flavor enhancer; may cause headaches in sensitive individuals.")
        
        # High sugar
        if any(x in ing for x in ["sugar", "fructose", "glucose", "syrup", "maltose", "dextrose", "sucrose"]):
            return (3, "Caution", "🍬 High sugar content; may contribute to obesity and diabetes.")
        
        # High sodium
        if any(x in ing for x in ["salt", "sodium"]):
            return (4, "Caution", "🧂 High sodium content; may raise blood pressure.")
        
        # High fat
        if any(x in ing for x in ["oil", "fat", "butter", "cream", "hydrogenated", "trans fat"]):
            return (4, "Caution", "🧈 High fat content; consume moderately.")
        
        # Trans fats (very harmful)
        if any(x in ing for x in ["hydrogenated", "trans fat", "partially hydrogenated"]):
            return (1, "Avoid", "❌ Contains trans fats; linked to heart disease.")
        
        # Healthy ingredients
        if any(x in ing for x in ["vitamin", "mineral", "protein", "fiber", "fibre"]):
            return (8, "Healthy", "✅ Fortified with nutrients; beneficial for health.")
        
        if any(x in ing for x in ["extract", "herb", "spice", "natural", "fruit", "vegetable", "leaf", "whole grain"]):
            return (8, "Healthy", "🌿 Natural ingredient; generally beneficial.")
        
        # Neutral/unknown
        return (5, "Unknown", "❓ Ingredient not recognized; neutral impact assumed.")

    # ===============================
    # MAIN ANALYSIS FUNCTION
    # ===============================
    def analyze_product(self, raw_text, product_name="Unknown Product"):
        """Analyze complete food product and return comprehensive health report."""
        
        # Clean text
        cleaned = self.clean_ingredient_text(raw_text)
        ingredients = [i.strip() for i in cleaned.split(',') if i.strip() and len(i.strip()) > 2]
        
        if not ingredients:
            return {
                'error': 'No ingredients found in text',
                'final_score': 0,
                'recommendation': 'Unable to analyze'
            }
        
        # Analyze each ingredient
        ingredient_results = []
        total_weight = 0
        weighted_sum = 0
        found_avoid = False
        found_caution = False
        
        for ing in ingredients:
            result = self.get_ingredient_score_cached(ing)
            ingredient_results.append(result)
            
            score = result['score']
            label = result['label'].lower()
            
            # Track flags
            if label == "avoid":
                found_avoid = True
            elif label == "caution":
                found_caution = True
            
            # Weighted scoring
            if "healthy" in label:
                weight = 1.2
            elif "avoid" in label:
                weight = 0.5
            elif "caution" in label:
                weight = 0.8
            else:
                weight = 1.0
            
            weighted_sum += score * weight
            total_weight += weight
        
        # Calculate final score
        final_score = weighted_sum / total_weight if total_weight > 0 else 5
        
        # Apply penalties
        if found_avoid:
            final_score *= 0.7
        elif found_caution:
            final_score *= 0.85
        
        final_score = round(max(0, min(final_score, 10)), 2)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(final_score, found_avoid, found_caution)
        
        # Prepare output
        result = {
            'product_name': product_name,
            'final_score': final_score,
            'total_ingredients': len(ingredients),
            'recommendation': recommendation,
            'ingredients': ingredient_results,
            'flags': {
                'has_harmful': found_avoid,
                'has_caution': found_caution
            }
        }
        
        return result

    # ===============================
    # RECOMMENDATION GENERATOR
    # ===============================
    def _generate_recommendation(self, score, has_avoid, has_caution):
        """Generate health recommendation based on score."""
        if score >= 8:
            return "✅ Excellent Choice! This product is healthy and nutritious."
        elif score >= 6.5:
            return "👍 Good Choice! Generally safe but consume in moderation."
        elif score >= 5:
            return "⚠️ Moderate! Contains some ingredients to be cautious about."
        elif score >= 3:
            return "🚨 Poor Choice! Contains multiple harmful ingredients. Limit consumption."
        else:
            return "❌ Avoid! This product contains highly harmful ingredients."

    # ===============================
    # DISPLAY RESULTS
    # ===============================
    def print_report(self, result):
        """Print formatted analysis report."""
        print("\n" + "="*60)
        print("🔬 FOOD PRODUCT HEALTH ANALYSIS REPORT")
        print("="*60)
        print(f"📦 Product: {result['product_name']}")
        print(f"🎯 Health Score: {result['final_score']}/10")
        print(f"📊 Ingredients Analyzed: {result['total_ingredients']}")
        print(f"💡 Recommendation: {result['recommendation']}")
        print("="*60)
        
        print("\n📋 INGREDIENT BREAKDOWN:\n")
        for ing_data in result['ingredients']:
            emoji = "✅" if "healthy" in ing_data['label'].lower() else "⚠️" if "caution" in ing_data['label'].lower() else "❌" if "avoid" in ing_data['label'].lower() else "❓"
            print(f"{emoji} {ing_data['ingredient'].title()}")
            print(f"   └─ Score: {ing_data['score']}/10 | Label: {ing_data['label']}")
            print(f"   └─ {ing_data['remark']}")
            print(f"   └─ Matched via: {ing_data['method']}\n")
        
        print("="*60)

    # ===============================
    # EXPORT TO JSON (for mobile apps)
    # ===============================
    def export_json(self, result, filename="analysis_result.json"):
        """Export result as JSON for mobile app consumption."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Results exported to {filename}")


# ===============================
# EXAMPLE USAGE
# ===============================
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = FoodAnalyzer("food_ingridients.csv")
    
    # Example 1: Instant Noodles
    print("\n" + " ANALYZING: patanjalil")
    ocr_text_1 = """Water, Sugar, Skimmed Milk Powder, Glucose, Probiotic-Lactobacillus casei strain Shirota, CONTAINS NATURAL & NATURAL IDENTICAL FLAVOURS
            ALLERGEN INFORMATION: CONTAINS MILK PRODUCTS. """
    
    result_1 = analyzer.analyze_product(ocr_text_1, "Instant Noodles")
    analyzer.print_report(result_1)
    
    
    
    print("\n✅ Analysis complete! Ready for mobile integration.")