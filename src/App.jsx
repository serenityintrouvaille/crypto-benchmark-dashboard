import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, Users, Target, Activity, ShieldCheck, Zap } from 'lucide-react';
import { cryptoServices, sectors } from './data';
import './index.css';

const IconMap = {
  '송금 (Remittance)': Zap,
  '프로토콜 (Protocol)': ShieldCheck,
  '투자 (Investment)': TrendingUp,
  '금융 (Finance)': Activity,
  'DeFi (Decentralized Finance)': Target,
  '스테이블코인 (Stablecoin)': Users
};

function App() {
  const [activeSector, setActiveSector] = useState('모두보기');
  const [selectedService, setSelectedService] = useState(null);

  const filteredServices = activeSector === '모두보기' 
    ? cryptoServices 
    : cryptoServices.filter(s => s.sector === activeSector);

  const openModal = (service) => {
    setSelectedService(service);
    document.body.style.overflow = 'hidden';
  };

  const closeModal = () => {
    setSelectedService(null);
    document.body.style.overflow = 'auto';
  };

  const renderList = (items) => {
    if (!items || items.length === 0) return null;
    return (
      <ul style={{ paddingLeft: '20px', marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {items.map((item, idx) => (
          <li key={idx} style={{ lineHeight: '1.5' }}>{item}</li>
        ))}
      </ul>
    );
  };

  return (
    <div className="container">
      <header className="header">
        <motion.h1 
          initial={{ y: -20, opacity: 0 }} 
          animate={{ y: 0, opacity: 1 }}
        >
          Crypto Benchmark Dashboard
        </motion.h1>
        <motion.p 
          initial={{ y: -20, opacity: 0 }} 
          animate={{ y: 0, opacity: 1 }} 
          transition={{ delay: 0.1 }}
        >
          매일 업데이트되는 글로벌 크립토/웹3 프로덕트 최신 트렌드 & UX 벤치마크
        </motion.p>
      </header>

      {/* Sector Filters */}
      <motion.div 
        className="filter-container"
        initial={{ y: 20, opacity: 0 }} 
        animate={{ y: 0, opacity: 1 }} 
        transition={{ delay: 0.2 }}
      >
        {sectors.map(sector => (
          <button 
            key={sector}
            className={`filter-btn ${activeSector === sector ? 'active' : ''}`}
            onClick={() => setActiveSector(sector)}
          >
            {sector.split(' ')[0]} {/* Show only the Korean part in the button for cleanlyness if desired, or all */}
          </button>
        ))}
      </motion.div>

      {/* Grid of Trending Products */}
      <motion.div layout className="grid">
        <AnimatePresence>
          {filteredServices.map((service, index) => {
            const Icon = IconMap[service.sector] || TrendingUp;
            // map sector color class name securely
            const sectorClass = service.sector.split(' ')[0];
            return (
              <motion.div
                key={service.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3 }}
                className="card"
                onClick={() => openModal(service)}
              >
                <div className="card-header">
                  <span className={`sector-badge sector-general`}>
                    {service.sector.split(' ')[0]}
                  </span>
                  <Icon size={24} color="var(--text-main)" />
                </div>
                <h2>{service.name}</h2>
                <p className="description">{service.description}</p>
                
                <div className="card-footer" style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Activity size={18} /> 상세 벤치마크
                  </span>
                  {service.link && service.link !== '#' && (
                    <a 
                      href={service.link} 
                      target="_blank" 
                      rel="noreferrer" 
                      onClick={(e) => e.stopPropagation()} 
                      style={{ fontSize: '0.85rem', color: 'var(--text-light)', textDecoration: 'underline' }}
                    >
                      기사 원문 ↗
                    </a>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </motion.div>

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedService && (
          <motion.div 
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeModal}
          >
            <motion.div 
              className="modal-content"
              initial={{ y: 50, opacity: 0, scale: 0.95 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 50, opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
            >
              <button className="close-btn" onClick={closeModal}>✕</button>
              
              <div className="modal-header">
                <span className={`sector-badge sector-general`}>
                  {selectedService.sector}
                </span>
                <h1 style={{ marginTop: '10px' }}>{selectedService.name}</h1>
                <p style={{ fontSize: '1.2rem', color: 'var(--text-light)', marginTop: '5px' }}>
                  {selectedService.description}
                </p>
              </div>

              <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
                <div style={{ flex: '1 1 300px' }}>
                  <img 
                    src={selectedService.image} 
                    alt={`${selectedService.name} UI Mockup`} 
                    style={{ width: '100%', borderRadius: '16px', border: '3px solid var(--text-main)', boxShadow: '8px 8px 0 rgba(0,0,0,0.1)' }}
                  />
                </div>
                <div style={{ flex: '2 1 400px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div className="data-item">
                    <h3><Zap size={20} /> User Experience (사용자 경험 및 금융적 장점)</h3>
                    {renderList(selectedService.uxHighlights)}
                  </div>
                  <div className="data-item">
                    <h3><Activity size={20} /> Business Structure (수익 구조)</h3>
                    {renderList(selectedService.businessStructure)}
                  </div>
                </div>
              </div>

              <div className="data-grid">
                <div className="data-item">
                  <h3><TrendingUp size={20} /> Revenue & Metrics (영업/고객 지표)</h3>
                  {renderList(selectedService.metrics)}
                </div>
                <div className="data-item">
                  <h3><ShieldCheck size={20} /> Investment (투자 유치)</h3>
                  {renderList(selectedService.funding)}
                </div>
                <div className="data-item">
                  <h3><Users size={20} /> Team Info (팀 정보)</h3>
                  {renderList(selectedService.teamInfo)}
                </div>
                <div className="data-item">
                  <h3><Target size={20} /> Similar Services (유사 서비스)</h3>
                  {renderList(selectedService.similarServices)}
                </div>
              </div>

            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
