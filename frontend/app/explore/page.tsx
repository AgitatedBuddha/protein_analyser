'use client';

import React from 'react';
import Navigation from '../../components/Navigation';
import AskData from '../../components/AskData';

export default function ExplorePage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto">
        
        <header className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Explore the Data</h1>
          <p className="text-gray-400">Ask questions in plain English to find the perfect protein for you.</p>
        </header>

        <Navigation />

        <div className="bg-black/20 rounded-2xl p-6 md:p-10 border border-gray-800">
          <div className="mb-8 text-center">
            <h2 className="text-2xl font-semibold text-white mb-2">What are you looking for?</h2>
            <p className="text-gray-400 text-sm">
              We use AI to translate your question into data filters. <br/>
              <span className="text-xs text-gray-500 uppercase tracking-widest mt-1 inline-block">Powered by Gemini Flash (Free Tier)</span>
            </p>
          </div>
          
          <AskData />
        </div>
        
      </div>
    </div>
  );
}
