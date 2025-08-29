import React, { useState } from 'react';
import { Card, Badge, Button, Modal, Tabs, Tab } from 'react-bootstrap';
import DOMPurify from 'dompurify';
import { marked } from 'marked';

interface Answer {
  text: string;
  page: number;
  module: string;
  score: number;
  is_xml: boolean;
  formatted_xml?: string;
  translated_text?: string;
}

interface SearchResultsProps {
  results: Answer[];
  translate: boolean;
}

const SearchResults: React.FC<SearchResultsProps> = ({ results, translate }) => {
  const [selectedXml, setSelectedXml] = useState<string | null>(null);
  const [showXmlModal, setShowXmlModal] = useState(false);

  const handleShowXml = (xml: string) => {
    setSelectedXml(xml);
    setShowXmlModal(true);
  };

  const handleCloseXmlModal = () => {
    setShowXmlModal(false);
    setSelectedXml(null);
  };

  // Function to safely convert Markdown to HTML
  const renderMarkdown = (text: string) => {
    const html = marked(text);
    return { __html: DOMPurify.sanitize(html) };
  };

  return (
    <>
      {results.map((result, index) => (
        <Card key={index} className="mb-4">
          <Card.Body>
            <div className="d-flex justify-content-between align-items-start mb-2">
              <div>
                <Badge bg="secondary" className="me-2">Sayfa {result.page}</Badge>
                {result.module && <Badge bg="info" className="me-2">Modül: {result.module}</Badge>}
                <Badge bg="light" text="dark">Skor: {(result.score * 100).toFixed(2)}%</Badge>
              </div>
              {result.is_xml && result.formatted_xml && (
                <Button 
                  variant="outline-secondary" 
                  size="sm" 
                  onClick={() => handleShowXml(result.formatted_xml!)}
                >
                  XML Görüntüle
                </Button>
              )}
            </div>
            
            {translate && result.translated_text ? (
              <Tabs
                defaultActiveKey="english"
                className="mb-3"
              >
                <Tab eventKey="english" title="İngilizce">
                  <div className="result-text" dangerouslySetInnerHTML={renderMarkdown(result.text)} />
                </Tab>
                <Tab eventKey="turkish" title="Türkçe">
                  <div className="result-text" dangerouslySetInnerHTML={renderMarkdown(result.translated_text)} />
                </Tab>
              </Tabs>
            ) : (
              <div className="result-text" dangerouslySetInnerHTML={renderMarkdown(result.text)} />
            )}
          </Card.Body>
        </Card>
      ))}

      <Modal 
        show={showXmlModal} 
        onHide={handleCloseXmlModal}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>XML İçeriği</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <pre className="xml-content">
            {selectedXml}
          </pre>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseXmlModal}>
            Kapat
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default SearchResults; 