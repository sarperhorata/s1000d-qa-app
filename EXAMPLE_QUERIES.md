# S1000D QA System - Örnek Sorgular ve Kullanım Kılavuzu

## 🎯 Genel Kullanım

### Temel Sorgular
```bash
# Basit metin sorgusu
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is S1000D?", "page_size": 5}'

# AI ile detaylı sorgu
curl -X POST "http://localhost:8000/ai-query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain S1000D in simple terms", "context_limit": 10}'
```

### Filtreleme ile Gelişmiş Sorgular

```bash
# Sadece belirli bir bölüm
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "business rules",
    "filter_chapter": "2.5",
    "page_size": 10
  }'

# Sadece tabloları ara
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "data structure",
    "filter_content_type": "table",
    "page_size": 5
  }'

# Sadece önemli sonuçlar (4+ yıldız)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "critical information",
    "min_importance": 4,
    "page_size": 10
  }'
```

## 📚 S1000D'ye Özel Sorgular

### 1. Genel Kavramlar
```bash
# S1000D nedir?
"What is S1000D?"

# S1000D bileşenleri nelerdir?
"What are the main components of S1000D?"

# S1000D versiyonları
"What are the different versions of S1000D?"
```

### 2. Business Rules (İş Kuralları)
```bash
# Business rules nedir?
"What are business rules in S1000D?"

# 13 adım business rules oluşturma
"Explain the 13 major steps in producing business rules"

# Business rules validation
"How to validate business rules?"

# BREX nedir?
"What is BREX in S1000D?"
```

### 3. Data Modules (Veri Modülleri)
```bash
# Data module code nedir?
"What is data module code?"

# Data module oluşturma
"How to create a data module?"

# Data module tipleri
"What are the types of data modules?"

# DMC formatı
"Explain DMC format"
```

### 4. Publication Modules (Yayın Modülleri)
```bash
# Publication module nedir?
"What is publication module?"

# PM code structure
"Explain publication module code structure"

# Publication module bileşenleri
"What are the components of publication module?"
```

### 5. CSDB (Common Source Database)
```bash
# CSDB nedir?
"What is CSDB?"

# CSDB gereksinimleri
"What are CSDB requirements?"

# CSDB data types
"What data types are stored in CSDB?"
```

### 6. Applicability (Uygulanabilirlik)
```bash
# Applicability nedir?
"What is applicability in S1000D?"

# Applicability statements
"How to create applicability statements?"

# Product applicability
"How to define product applicability?"
```

## 🔍 İleri Düzey Sorgular

### Kombine Filtreleme
```bash
# Belirli bölümde önemli tablolar
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "validation rules",
    "filter_chapter": "3",
    "filter_content_type": "table",
    "min_importance": 3,
    "page_size": 10
  }'
```

### İçerik Tipine Göre Arama
```bash
# Sadece başlıklar
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "requirements",
    "filter_content_type": "heading",
    "page_size": 20
  }'

# Sadece diyagramlar (OCR ile)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "assembly diagram",
    "filter_content_type": "diagram",
    "page_size": 5
  }'
```

### Önem Derecesine Göre Sıralama
```bash
# Sadece kritik bilgiler (5 yıldız)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mandatory requirements",
    "min_importance": 5,
    "page_size": 10
  }'

# Önemli bilgiler (4+ yıldız)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "best practices",
    "min_importance": 4,
    "page_size": 15
  }'
```

## 🤖 AI Destekli Sorgular

### Karmaşık Sorular
```bash
# S1000D implementasyon adımları
curl -X POST "http://localhost:8000/ai-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the steps to implement S1000D in an organization?",
    "context_limit": 20
  }'

# Business rules vs validation rules karşılaştırması
curl -X POST "http://localhost:8000/ai-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare business rules and validation rules in S1000D",
    "context_limit": 15
  }'
```

### Teknik Detaylar
```bash
# XML schema yapısı
curl -X POST "http://localhost:8000/ai-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the XML schema structure used in S1000D data modules",
    "context_limit": 25
  }'

# Metadata gereksinimleri
curl -X POST "http://localhost:8000/ai-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What metadata is required for S1000D data modules?",
    "context_limit": 20
  }'
```

## 📊 Performans Test Sorguları

### Hız Testi
```bash
# Basit sorgu hızı
time curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "S1000D", "page_size": 5}' > /dev/null

# Karmaşık sorgu hızı
time curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "business rules validation process",
    "filter_chapter": "2.5",
    "min_importance": 3,
    "page_size": 10
  }' > /dev/null
```

### Doğruluk Testi
```bash
# Test sorguları
declare -a queries=(
  "What is S1000D?"
  "Explain DMC structure"
  "How to create business rules?"
  "What is the difference between data module and publication module?"
  "Explain S1000D issue 6 features"
)

for query in "${queries[@]}"; do
  echo "Testing: $query"
  curl -s -X POST "http://localhost:8000/query" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\", \"page_size\": 3}" | \
    python -c "
import sys, json
data = json.load(sys.stdin)
print(f'Results: {data[\"answer_count\"]}')
print(f'Top score: {data[\"answers\"][0][\"score\"]:.3f}')
print(f'Content type: {data[\"answers\"][0].get(\"content_type\", \"unknown\")}')
print('---')
"
done
```

## 🎨 Frontend Kullanım Örnekleri

### React/TypeScript ile Sorgu
```typescript
import axios from 'axios';

interface SearchRequest {
  query: string;
  page?: number;
  page_size?: number;
  filter_chapter?: string;
  filter_content_type?: string;
  min_importance?: number;
}

const searchDocuments = async (request: SearchRequest) => {
  const response = await axios.post('/query', request);
  return response.data;
};

// Kullanım örneği
const results = await searchDocuments({
  query: "business rules",
  filter_chapter: "2.5",
  filter_content_type: "table",
  min_importance: 3,
  page_size: 10
});
```

### Filtreleme UI Örneği
```typescript
// Bölüm filtresi
<Form.Control
  placeholder="Bölüm (örn: 2.5)"
  value={filterChapter}
  onChange={(e) => setFilterChapter(e.target.value)}
/>

// İçerik tipi filtresi
<Form.Select value={filterContentType} onChange={(e) => setFilterContentType(e.target.value)}>
  <option value="">Tümü</option>
  <option value="text">Metin</option>
  <option value="heading">Başlık</option>
  <option value="table">Tablo</option>
  <option value="diagram">Diyagram</option>
  <option value="list">Liste</option>
</Form.Select>

// Önem derecesi filtresi
<Form.Select value={minImportance} onChange={(e) => setMinImportance(Number(e.target.value))}>
  <option value={1}>1+ (Tümü)</option>
  <option value={2}>2+ (Önemli)</option>
  <option value={3}>3+ (Çok Önemli)</option>
  <option value={4}>4+ (Kritik)</option>
  <option value={5}>5 (En Kritik)</option>
</Form.Select>
```

## 📈 Sorgu Kalitesi Ölçütleri

### İyi Sonuç Kriterleri
- ✅ **Score > 0.6**: Çok alakalı
- ✅ **Score 0.4-0.6**: Alakalı
- ✅ **Score 0.2-0.4**: Kısmen alakalı
- ❌ **Score < 0.2**: Zayıf sonuç

### İçerik Tipi Dağılımı (Hedef)
- 📝 **Text**: 70% - Ana içerikler
- 📋 **Heading**: 15% - Başlıklar ve bölümler
- 📊 **Table**: 10% - Tablolar ve listeler
- 🎨 **Diagram**: 5% - Teknik diyagramlar

### Önem Derecesi Dağılımı
- ⭐ **5 yıldız**: Kritik, standart tanımları
- ⭐⭐ **4 yıldız**: Önemli prosedürler
- ⭐⭐⭐ **3 yıldız**: Genel bilgiler
- ⭐⭐ **2 yıldız**: Destekleyici detaylar
- ⭐ **1 yıldız**: Genel metinler

## 🔧 Sorun Giderme

### Zayıf Sonuçlar Alıyorsanız

```bash
# 1. Filtreleri kaldırın
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "your query", "page_size": 20}'

# 2. Anahtar kelimeleri değiştirin
# "business rules" yerine "business rule" deneyin

# 3. Daha genel sorgu kullanın
# "S1000D issue 6 business rules" yerine "S1000D business rules"

# 4. Sayfa sayısını artırın
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "your query", "page_size": 50}'
```

### Hızlı Sorgular
```bash
# Basit sorgu hızı
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "S1000D", "page_size": 5}'

# Filtreli sorgu hızı
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "data module",
    "filter_chapter": "3",
    "page_size": 10
  }'
```

## 📚 En İyi Uygulamalar

### Sorgu Yazma
1. **Anahtar kelimeleri kullanın**: "S1000D", "business rules", "data module"
2. **Belirli terimler kullanın**: "DMC", "BREX", "CSDB", "applicability"
3. **Bölüm numaraları ekleyin**: "Chapter 2.5 business rules"

### Filtreleme Stratejileri
1. **Önce genel arama yapın**, sonra filtreleyin
2. **İlk 20 sonucu inceleyin**, desenleri bulun
3. **İlgili bölümleri tespit edin**, sonra o bölümü filtreleyin
4. **İçerik tiplerini anlayın**: tablolar teknik detaylar, başlıklar yapı

### Performans İçin
1. **Makül sayfa boyutları kullanın**: 5-20 arası
2. **Gereksiz filtrelerden kaçının**
3. **AI sorgularını akıllıca kullanın**: karmaşık sorular için

---

## 🎯 Hızlı Başvuru

### En Sık Kullanılan Sorgular
- `"What is S1000D?"` - Genel tanım
- `"Explain DMC structure"` - Data module code
- `"business rules in S1000D"` - İş kuralları
- `"S1000D data modules"` - Veri modülleri
- `"publication module requirements"` - Yayın modülleri

### Hızlı Filtreler
- `filter_chapter: "2.5"` - Business rules bölümü
- `filter_content_type: "table"` - Sadece tablolar
- `min_importance: 4` - Sadece önemli bilgiler

### Performans Hedefleri
- **Latency**: <500ms
- **Relevance**: >0.6 score
- **Coverage**: Tüm içerik tipleri

---

**Son Güncelleme:** 17 Ekim 2025
**Versiyon:** v2.0
**API:** Enhanced endpoints ✅
**Frontend:** Updated with filters ✅


