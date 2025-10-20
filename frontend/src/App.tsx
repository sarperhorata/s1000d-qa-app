import React, { useState } from 'react';
import { Container, Row, Col, Form, Button, Alert, Card, Badge, Spinner, Pagination } from 'react-bootstrap';
import axios from 'axios';
import './App.css';

// Define the API response types
interface Answer {
  text: string;
  page: number;
  module: string;
  score: number;
  is_xml: boolean;
  formatted_xml?: string;
  translated_text?: string;
  content_type?: string;  // NEW: Content type (text, heading, table, diagram, list)
  importance?: number;    // NEW: Importance score (1-5)
}

interface SummaryResponse {
  summary: string;
  is_comprehensive: boolean;
}

interface QueryResponse {
  answers: Answer[];
  answer_count: number;
  total_results: number;
  current_page: number;
  total_pages: number;
  summary?: SummaryResponse;
  search_time: number;
}

interface ImageData {
  page: number;
  index: number;
  format: string;
  data: string;
  size: number;
}

interface ImagesResponse {
  status: string;
  query: string;
  images: ImageData[];
  total_images: number;
}

// Axios configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
axios.defaults.baseURL = API_BASE_URL;
axios.defaults.withCredentials = true;
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.headers.common['Accept'] = 'application/json';
axios.defaults.xsrfCookieName = 'XSRF-TOKEN';
axios.defaults.xsrfHeaderName = 'X-XSRF-TOKEN';

function App() {
  // State variables
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<QueryResponse | null>(null);
  const [aiResponse, setAiResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [translate, setTranslate] = useState<boolean>(true);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [summaryMode, setSummaryMode] = useState<boolean>(true);
  const [images, setImages] = useState<ImageData[]>([]);
  const [showImages, setShowImages] = useState<boolean>(true);
  const [loadingImages, setLoadingImages] = useState<boolean>(false);
  const [summary, setSummary] = useState<string>('');
  const [quickMode, setQuickMode] = useState<boolean>(true);
  const [aiMode, setAiMode] = useState<boolean>(true);
  const [searchTime, setSearchTime] = useState(0);
  const [backendStatus, setBackendStatus] = useState<'unknown' | 'ok' | 'error'>('unknown');

  // NEW: Advanced filtering
  const [filterChapter, setFilterChapter] = useState<string>('');
  const [filterContentType, setFilterContentType] = useState<string>('');
  const [minImportance, setMinImportance] = useState<number>(1);

  // API base URL
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Check backend status on load
  React.useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        await axios.get(`${API_BASE_URL}/health`);
        setBackendStatus('ok');
      } catch (error) {
        console.error("Backend connection error:", error);
        setBackendStatus('error');
        setError("Backend sunucusuna bağlanılamıyor. Lütfen sunucunun çalıştığından emin olun.");
      }
    };
    
    checkBackendStatus();
  }, [API_BASE_URL]);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    // Reset filters on new search
    setFilterChapter('');
    setFilterContentType('');
    setMinImportance(1);

    setIsLoading(true);
    setError(null);
    setResults(null);
    setAiResponse('');
    setSummary('');
    setSearchTime(0);

    try {
      const response = await axios.post<QueryResponse>(`${API_BASE_URL}/query`, {
        query,
        page: 1,
        page_size: 10,
        translate: false,
        language: 'en',
        summary_mode: false,
        skip_search: false,
        filter_chapter: filterChapter || undefined,
        filter_content_type: filterContentType || undefined,
        min_importance: minImportance > 1 ? minImportance : undefined
      }, {
        headers: {
          'Content-Type': 'application/json',
          'X-XSRF-TOKEN': 'xsrf-token'
        },
        withCredentials: true
      });

      if (response.data) {
        setResults(response.data);
        if (response.data.answers && response.data.answers.length > 0) {
          setAiResponse(response.data.answers[0].text || '');
        } else {
          setAiResponse('No results found for your query. Please try a different search term.');
        }
        setSummary(response.data.summary?.summary || '');
        setSearchTime(response.data.search_time || 0);

        // Fetch related images
        await fetchImages(query);
      }
    } catch (error) {
      console.error('Search failed:', error);
      if (axios.isAxiosError(error) && error.response) {
        setError(`Error: ${error.response.data.detail || error.message}`);
      } else {
        setError('Failed to get search results. Please try again.');
      }
      setAiResponse('An error occurred while searching. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch images for query
  const fetchImages = async (searchQuery: string) => {
    if (!showImages) return;

    setLoadingImages(true);
    try {
      const response = await axios.get<ImagesResponse>(`${API_BASE_URL}/get-images-for-query`, {
        params: {
          query: searchQuery,
          limit: 5
        },
        headers: {
          'X-XSRF-TOKEN': 'xsrf-token'
        },
        withCredentials: true
      });

      if (response.data && response.data.status === 'success') {
        setImages(response.data.images);
      }
    } catch (error) {
      console.error('Failed to fetch images:', error);
      setImages([]);
    } finally {
      setLoadingImages(false);
    }
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);

    // Page değiştiğinde yeni sorgu yap
    const fetchPage = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await axios.post<QueryResponse>(`${API_BASE_URL}/query`, {
          query,
          translate,
          page,
          page_size: 10,
          summary_mode: summaryMode,
          quick_mode: quickMode,
          filter_chapter: filterChapter || undefined,
          filter_content_type: filterContentType || undefined,
          min_importance: minImportance > 1 ? minImportance : undefined
        }, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-XSRF-TOKEN': 'xsrf-token'
          },
          withCredentials: true
        });
        
        setResults(response.data);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response) {
          setError(`Hata: ${err.response.data.detail || err.message}`);
        } else {
          setError(`Hata: ${(err as Error).message}`);
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchPage();
  };

  // Pagination için sayfa numaralarını oluştur
  const renderPaginationItems = () => {
    if (!results) return null;
    
    const items = [];
    const maxVisiblePages = 5;
    const totalPages = results.total_pages;
    
    // İlk sayfa
    items.push(
      <Pagination.Item 
        key="first" 
        onClick={() => handlePageChange(1)} 
        disabled={currentPage === 1}
      >
        İlk
      </Pagination.Item>
    );
    
    // Önceki sayfa
    items.push(
      <Pagination.Item 
        key="prev" 
        onClick={() => handlePageChange(Math.max(1, currentPage - 1))} 
        disabled={currentPage === 1}
      >
        &laquo;
      </Pagination.Item>
    );
    
    // Görünür sayfa numaraları
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Maksimum görünür sayfa sayısına ulaşmak için başlangıcı ayarla
    if (endPage - startPage + 1 < maxVisiblePages && startPage > 1) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      items.push(
        <Pagination.Item 
          key={i} 
          active={i === currentPage} 
          onClick={() => handlePageChange(i)}
        >
          {i}
        </Pagination.Item>
      );
    }
    
    // Sonraki sayfa
    items.push(
      <Pagination.Item 
        key="next" 
        onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))} 
        disabled={currentPage === totalPages}
      >
        &raquo;
      </Pagination.Item>
    );
    
    // Son sayfa
    items.push(
      <Pagination.Item 
        key="last" 
        onClick={() => handlePageChange(totalPages)} 
        disabled={currentPage === totalPages}
      >
        Son
      </Pagination.Item>
    );
    
    return items;
  };

  // Render AI response
  const renderAIResponse = () => {
    if (!aiResponse) return null;

    return (
      <div className="ai-response">
        <h3>Search Results</h3>
        <div className="response-content">
          {aiResponse.split('\n').map((paragraph: string, index: number) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>
        {summary && (
          <div className="summary">
            <h4>Summary</h4>
            <p>{summary}</p>
          </div>
        )}
        {searchTime > 0 && (
          <div className="search-stats">
            <p>Search Time: {searchTime.toFixed(2)}s</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <Container className="py-5">
      <Row className="mb-4">
        <Col>
          <h1 className="text-center">S1000D Doküman Sorgulama</h1>
          <p className="text-center text-muted">
            S1000D dokümantasyonunu arayın ve sorularınıza anında cevap alın
          </p>
          {backendStatus === 'error' && (
            <Alert variant="danger" className="text-center">
              Backend sunucusuna bağlantı kurulamıyor. Lütfen sunucunun çalıştığından emin olun.
            </Alert>
          )}
        </Col>
      </Row>

      <Row className="justify-content-center mb-4">
        <Col md={10}>
          <Card>
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Sorgunuzu yazın:</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={6}
                    placeholder="Sorgunuzu buraya yazın (örn: 'What are the main components of an information set?')"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    maxLength={4096}
                    disabled={isLoading}
                  />
                  <Form.Text className="text-muted">
                    İngilizce olarak soru sorun veya anahtar kelimeler girin.
                  </Form.Text>
                </Form.Group>

                {/* NEW: Advanced Filtering Section */}
                <Form.Group className="mb-3">
                  <Form.Label className="text-primary">
                    <i className="bi bi-funnel me-2"></i>
                    Gelişmiş Filtreleme (İsteğe Bağlı)
                  </Form.Label>
                  <Row>
                    <Col md={4}>
                      <Form.Control
                        type="text"
                        placeholder="Bölüm (örn: 2.5, 3.1)"
                        value={filterChapter}
                        onChange={(e) => setFilterChapter(e.target.value)}
                        disabled={isLoading}
                      />
                    </Col>
                    <Col md={4}>
                      <Form.Select
                        value={filterContentType}
                        onChange={(e) => setFilterContentType(e.target.value)}
                        disabled={isLoading}
                      >
                        <option value="">İçerik Tipi (Hepsi)</option>
                        <option value="text">Metin</option>
                        <option value="heading">Başlık</option>
                        <option value="table">Tablo</option>
                        <option value="diagram">Diyagram</option>
                        <option value="list">Liste</option>
                      </Form.Select>
                    </Col>
                    <Col md={4}>
                      <Form.Select
                        value={minImportance}
                        onChange={(e) => setMinImportance(Number(e.target.value))}
                        disabled={isLoading}
                      >
                        <option value={1}>Önem Derecesi (1+)</option>
                        <option value={2}>Önem Derecesi (2+)</option>
                        <option value={3}>Önem Derecesi (3+)</option>
                        <option value={4}>Önem Derecesi (4+)</option>
                        <option value={5}>Önem Derecesi (5)</option>
                      </Form.Select>
                    </Col>
                  </Row>
                  <Form.Text className="text-muted">
                    Bölüm, içerik tipi veya önem derecesine göre sonuçları filtreleyin.
                  </Form.Text>
                  {(filterChapter || filterContentType || minImportance > 1) && (
                    <Button
                      variant="outline-secondary"
                      size="sm"
                      className="mt-2"
                      onClick={() => {
                        setFilterChapter('');
                        setFilterContentType('');
                        setMinImportance(1);
                      }}
                    >
                      <i className="bi bi-x-circle me-1"></i>
                      Filtreleri Temizle
                    </Button>
                  )}
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Yapay Zeka ile yanıtla"
                    checked={aiMode}
                    onChange={(e) => setAiMode(e.target.checked)}
                    id="ai-mode-checkbox"
                    disabled={isLoading}
                  />
                  <Form.Text className="text-muted">
                    OpenAI kullanarak sorularınızı doğrudan cevaplandırır.
                  </Form.Text>
                </Form.Group>

                {!aiMode && (
                  <>
                    <Row className="mb-3">
                      <Col md={6}>
                        <Form.Check
                          type="checkbox"
                          label="Türkçe çevirileri göster"
                          checked={translate}
                          onChange={(e) => setTranslate(e.target.checked)}
                          id="translate-checkbox"
                          disabled={isLoading}
                        />
                      </Col>
                      <Col md={6}>
                        <Form.Check
                          type="checkbox"
                          label="Özet cevap göster"
                          checked={summaryMode}
                          onChange={(e) => setSummaryMode(e.target.checked)}
                          id="summary-checkbox"
                          disabled={isLoading}
                        />
                      </Col>
                    </Row>
                    
                    <Form.Group className="mb-3">
                      <Form.Check
                        type="checkbox"
                        label="Hızlı arama modu (varsayılan)"
                        checked={quickMode}
                        onChange={(e) => setQuickMode(e.target.checked)}
                        id="quick-mode-checkbox"
                        disabled={isLoading}
                      />
                      <Form.Text className="text-muted">
                        Hızlı arama tüm dokümanı tarar ama işlemi optimize eder.
                      </Form.Text>
                    </Form.Group>
                  </>
                )}

                <div className="d-grid">
                  <Button 
                    variant="primary" 
                    type="submit" 
                    disabled={isLoading || !query.trim() || backendStatus === 'error'} 
                    className="search-button"
                  >
                    {isLoading ? (
                      <>
                        <Spinner
                          as="span"
                          animation="border"
                          size="sm"
                          role="status"
                          aria-hidden="true"
                          className="me-2"
                        />
                        {aiMode ? 'AI yanıtı oluşturuluyor...' : 'Aranıyor...'}
                      </>
                    ) : (
                      aiMode ? 'AI ile Yanıtla' : 'Ara'
                    )}
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {error && (
        <Row className="justify-content-center mb-4">
          <Col md={10}>
            <Alert variant="danger">{error}</Alert>
          </Col>
        </Row>
      )}

      {isLoading && (
        <Row className="justify-content-center my-5">
          <Col md={10} className="text-center">
            <Spinner animation="border" role="status" variant="primary" style={{ width: '3rem', height: '3rem' }}>
              <span className="visually-hidden">Aranıyor...</span>
            </Spinner>
            <p className="mt-3">
              {aiMode 
                ? 'S1000D dokümanlarında araştırılıyor ve AI yanıtı hazırlanıyor...' 
                : 'S1000D dokümanları aranıyor. Lütfen bekleyin...'}
            </p>
          </Col>
        </Row>
      )}

      {/* AI Response Display */}
      {!isLoading && aiResponse && (
        <Row className="justify-content-center">
          <Col md={10}>
            {renderAIResponse()}
          </Col>
        </Row>
      )}

      {/* Regular Search Results Display */}
      {!isLoading && !aiMode && results && summary && (
        <Row className="justify-content-center mb-4">
          <Col md={10}>
            <Card className="summary-card">
              <Card.Body>
                <Card.Title>
                  <i className="bi bi-lightbulb me-2"></i>
                  Kısa Özet
                </Card.Title>
                <Card.Text>{summary}</Card.Text>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {!isLoading && !aiMode && results && (
        <Row className="justify-content-center">
          <Col md={10}>
            <Card className="mb-4">
              <Card.Body>
                <h5>
                  <Badge bg="primary" className="me-2">{results.answer_count}</Badge>
                  sonuç bulundu - Sayfa {currentPage}/{results.total_pages}
                  {searchTime > 0 && (
                    <span className="search-time ms-2">
                      <i className="bi bi-clock"></i> {searchTime.toFixed(2)} saniye
                    </span>
                  )}
                </h5>

                {/* NEW: Show active filters */}
                {(filterChapter || filterContentType || minImportance > 1) && (
                  <div className="mb-2">
                    <small className="text-muted">
                      Aktif Filtreler:
                      {filterChapter && <Badge bg="info" className="ms-1">Bölüm: {filterChapter}</Badge>}
                      {filterContentType && <Badge bg="success" className="ms-1">
                        {filterContentType === 'heading' ? 'Başlık' :
                         filterContentType === 'table' ? 'Tablo' :
                         filterContentType === 'diagram' ? 'Diyagram' :
                         filterContentType === 'list' ? 'Liste' : 'Metin'}
                      </Badge>}
                      {minImportance > 1 && <Badge bg="warning" className="ms-1">Önem: {minImportance}+</Badge>}
                    </small>
                  </div>
                )}
                
                {results.total_pages > 1 && (
                  <div className="mt-3 d-flex justify-content-center">
                    <Pagination>
                      {renderPaginationItems()}
                    </Pagination>
                  </div>
                )}
              </Card.Body>
            </Card>
            
            {results.answers.map((answer, index) => (
              <Card key={index} className="mb-3">
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-start mb-2">
                    <div>
                      <Badge bg="secondary" className="me-2">Sayfa {answer.page}</Badge>
                      {answer.module && <Badge bg="info" className="me-2">{answer.module}</Badge>}
                      <Badge bg="light" text="dark">Benzerlik: {(answer.score * 100).toFixed(1)}%</Badge>
                      {answer.content_type && (
                        <Badge bg="success" className="me-2">
                          {answer.content_type === 'heading' ? 'Başlık' :
                           answer.content_type === 'table' ? 'Tablo' :
                           answer.content_type === 'diagram' ? 'Diyagram' :
                           answer.content_type === 'list' ? 'Liste' : 'Metin'}
                        </Badge>
                      )}
                      {answer.importance && answer.importance >= 4 && (
                        <Badge bg="warning" className="me-2">
                          ⭐ Önemli ({answer.importance}/5)
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Card.Text>{answer.text}</Card.Text>
                  {answer.translated_text && translate && (
                    <Card.Text className="mt-2 text-muted">
                      <small>{answer.translated_text}</small>
                    </Card.Text>
                  )}
                </Card.Body>
              </Card>
            ))}
          </Col>
        </Row>
      )}

      {/* Images Section */}
      {images.length > 0 && showImages && (
        <Row className="justify-content-center mt-4">
          <Col md={10}>
            <Card className="mb-4">
              <Card.Header>
                <div className="d-flex justify-content-between align-items-center">
                  <h5 className="mb-0">
                    <i className="bi bi-images me-2"></i>
                    İlgili Görseller ({images.length})
                  </h5>
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={() => setShowImages(!showImages)}
                  >
                    {showImages ? 'Gizle' : 'Göster'}
                  </Button>
                </div>
              </Card.Header>
              <Card.Body>
                {loadingImages ? (
                  <div className="text-center">
                    <Spinner animation="border" />
                    <p className="mt-2">Görseller yükleniyor...</p>
                  </div>
                ) : (
                  <Row>
                    {images.map((image, index) => (
                      <Col key={index} md={6} lg={4} className="mb-3">
                        <Card className="h-100">
                          <Card.Body className="p-2">
                            <img
                              src={image.data}
                              alt={`Sayfa ${image.page} - Görsel ${image.index + 1}`}
                              className="img-fluid rounded"
                              style={{ maxHeight: '200px', width: '100%', objectFit: 'contain' }}
                            />
                            <div className="mt-2">
                              <small className="text-muted">
                                <Badge bg="info" className="me-1">Sayfa {image.page}</Badge>
                                <Badge bg="secondary">#{image.index + 1}</Badge>
                                <span className="ms-2">
                                  {Math.round(image.size / 1024)} KB
                                </span>
                              </small>
                            </div>
                          </Card.Body>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Images Toggle Button */}
      {results && (
        <Row className="justify-content-center">
          <Col md={10}>
            <div className="text-center mb-4">
              <Button
                variant={showImages ? "outline-primary" : "outline-secondary"}
                onClick={() => setShowImages(!showImages)}
                disabled={loadingImages}
              >
                <i className="bi bi-images me-2"></i>
                Görseller {showImages ? 'Gizle' : 'Göster'}
                {loadingImages && <Spinner animation="border" size="sm" className="ms-2" />}
              </Button>
            </div>
          </Col>
        </Row>
      )}
    </Container>
  );
}

export default App;
