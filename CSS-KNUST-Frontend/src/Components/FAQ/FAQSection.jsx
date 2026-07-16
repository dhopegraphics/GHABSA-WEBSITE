import React from 'react';
import { FAQItem } from './FAQItem';

export function FAQSection({ category, icon: Icon, questions }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-50 rounded-lg">
          <Icon className="w-6 h-6 text-blue-600" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900">{category}</h2>
      </div>

      <div className="space-y-4">
        {questions.map((question, index) => (
          <FAQItem key={index} {...question} />
        ))}
      </div>
    </div>
  );
}