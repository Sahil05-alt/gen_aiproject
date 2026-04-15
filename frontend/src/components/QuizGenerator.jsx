import React, { useMemo, useState } from 'react';
import { generateQuiz } from '../utils/api';

const QUESTION_COUNTS = [3, 5, 7, 10];

function buildContext(citations) {
  return citations
    .map((citation) => {
      const docName = citation.doc_name || 'Unknown';
      const chunkIndex = citation.chunk_index ?? 0;
      const excerpt = citation.excerpt || '';
      return `[${docName}, chunk ${chunkIndex}]\n${excerpt}`;
    })
    .join('\n\n');
}

export default function QuizGenerator({ citations }) {
  const [numQuestions, setNumQuestions] = useState(5);
  const [quiz, setQuiz] = useState([]);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const context = useMemo(() => buildContext(citations || []), [citations]);
  const score = quiz.reduce((total, question, index) => {
    return total + (answers[index] === question.answer ? 1 : 0);
  }, 0);

  const handleGenerate = async () => {
    setIsLoading(true);
    try {
      const result = await generateQuiz(context, numQuestions);
      setQuiz(result.questions || []);
      setAnswers({});
      setSubmitted(false);
    } catch (error) {
      alert(`Quiz generation failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePick = (questionIndex, label) => {
    if (submitted) {
      return;
    }

    setAnswers((prev) => ({
      ...prev,
      [questionIndex]: label,
    }));
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto mt-6 bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">Quiz Generator</h3>
          <p className="text-sm text-slate-500">
            Create practice questions from the latest retrieved chunks.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            disabled={isLoading}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
          >
            {QUESTION_COUNTS.map((count) => (
              <option key={count} value={count}>
                {count} questions
              </option>
            ))}
          </select>
          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Generating...' : 'Generate Quiz'}
          </button>
        </div>
      </div>

      {quiz.length > 0 && (
        <div className="mt-6 space-y-5">
          {quiz.map((item, questionIndex) => (
            <div key={`${questionIndex}-${item.question}`} className="border border-slate-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-slate-800">
                {questionIndex + 1}. {item.question}
              </p>
              <div className="mt-3 grid gap-2">
                {item.options.map((option) => {
                  const selected = answers[questionIndex] === option.label;
                  const isCorrect = submitted && option.label === item.answer;
                  const isWrongPick = submitted && selected && option.label !== item.answer;

                  let className = 'border-slate-300 bg-white text-slate-700 hover:border-blue-400';
                  if (!submitted && selected) {
                    className = 'border-blue-500 bg-blue-50 text-blue-700';
                  }
                  if (isCorrect) {
                    className = 'border-green-500 bg-green-50 text-green-700';
                  }
                  if (isWrongPick) {
                    className = 'border-red-500 bg-red-50 text-red-700';
                  }

                  return (
                    <button
                      key={option.label}
                      onClick={() => handlePick(questionIndex, option.label)}
                      disabled={submitted}
                      className={`w-full text-left rounded-lg border px-3 py-2 text-sm transition-colors disabled:cursor-default ${className}`}
                    >
                      <span className="font-semibold mr-2">{option.label}.</span>
                      <span>{option.text}</span>
                    </button>
                  );
                })}
              </div>

              {submitted && (
                <div className="mt-3 space-y-1 text-sm">
                  <p className="text-slate-700">
                    <span className="font-semibold">Correct answer:</span> {item.answer}
                  </p>
                  <p className="text-slate-600">
                    <span className="font-semibold">Explanation:</span> {item.explanation}
                  </p>
                </div>
              )}
            </div>
          ))}

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pt-1">
            <button
              onClick={handleSubmit}
              disabled={submitted || quiz.length === 0}
              className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:bg-slate-300 disabled:cursor-not-allowed"
            >
              Submit Quiz
            </button>
            {submitted && (
              <p className="text-sm font-semibold text-slate-800">
                Final score: {score} / {quiz.length}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
