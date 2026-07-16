import React, { useState, useRef } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

export function FAQItem({ question, answer }) {
  const [isOpen, setIsOpen] = useState(false);
  const contentRef = useRef(null); 

  return (
    <div className="border border-gray-100 rounded-lg">
      
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors rounded-lg"
      >
        <span className="font-medium text-gray-900">{question}</span>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>

      <div
        style={{
          height: isOpen ? `${contentRef.current?.scrollHeight}px` : "0px",
          overflow: "hidden",
          transition: "height 0.3s ease",
        }}
        className="bg-gray-50 rounded-b-lg"
      >
        <div
          ref={contentRef} 
          className={`p-4 pt-0 text-gray-600 ${isOpen ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}
        >
          {answer}
        </div>
      </div>
    </div>
  );
}
