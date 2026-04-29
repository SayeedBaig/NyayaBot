import React, { useRef, useState } from "react";
import "./App.css";
import heroImage from "./assets/hero.png";
import { analyzeProblem, generateDocument, generateLegalReport, requestNextQuestion } from "./api/nyaybot";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";
import LanguageSelector from "./components/LanguageSelector";
import ResultPanel from "./components/ResultPanel";

const helpCards = [
  {
    title: "Legal Information",
    text: "Clear explanations about Indian laws, legal procedures, and rights in simple language.",
    icon: "i",
  },
  {
    title: "Document Guidance",
    text: "Understand notices, contracts, complaints, and forms with practical AI-powered summaries.",
    icon: "d",
  },
  {
    title: "Rights Awareness",
    text: "Learn the protections available to you before you decide the next step.",
    icon: "r",
  },
];

const topics = [
  ["Constitutional Law", "Fundamental rights, remedies, and duties"],
  ["Criminal Law", "IPC, CrPC, FIRs, bail, and police process"],
  ["Civil Law", "Contracts, disputes, property, and civil procedure"],
  ["Family Law", "Marriage, divorce, adoption, and succession"],
  ["Consumer Law", "Consumer protection and dispute resolution"],
  ["Labor Law", "Workplace rights and employment concerns"],
  ["Property Law", "Real estate, tenancy, and ownership issues"],
  ["Cyber Law", "Digital rights, online fraud, and cyber crimes"],
];

const samplePrompts = [
  "How do I file a consumer complaint?",
  "What should I do after online fraud?",
  "Explain tenant rights in simple words.",
];

const starterSuggestions = [
  "My employer didn't pay salary",
  "Landlord is forcing me to vacate",
  "I received a defective product",
];

const toList = (value) => {
  if (Array.isArray(value)) return value;
  if (!value) return [];
  return [value];
};

const createSessionId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
};

const getShortSummary = (data) => {
  const text = data.summary || data.short_response || data.response || "";
  if (text.length <= 180) return text;
  return `${text.slice(0, 177).trim()}...`;
};

const getInputPlaceholder = (question) => {
  if (!question) return "Describe your problem...";
  if (question.toLowerCase().includes("which city")) return "Enter your city...";
  return "Type your answer...";
};

const App = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [inputError, setInputError] = useState("");
  const [language, setLanguage] = useState("en");
  const [isLoading, setIsLoading] = useState(false);
  const [isGeneratingDocument, setIsGeneratingDocument] = useState(false);
  const [theme, setTheme] = useState("dark");
  const [resultData, setResultData] = useState(null);
  const [lastQuestion, setLastQuestion] = useState("");
  const [awaitingMoreDetails, setAwaitingMoreDetails] = useState(false);
  const [sessionId, setSessionId] = useState(() => createSessionId());
  const [currentFollowUpQuestion, setCurrentFollowUpQuestion] = useState("");
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const resultRef = useRef(null);
  const messageIdRef = useRef(0);

  const getMessageId = (prefix) => {
    messageIdRef.current += 1;
    return `${prefix}-${messageIdRef.current}`;
  };

  const handlePointerMove = (event) => {
    const x = `${event.clientX}px`;
    const y = `${event.clientY}px`;

    event.currentTarget.style.setProperty("--cursor-x", x);
    event.currentTarget.style.setProperty("--cursor-y", y);
  };

  const sendMessage = async (text) => {
    const cleanText = text.trim();
    if (!cleanText) {
      setInputError("Please describe your issue");
      return;
    }
    if (isLoading) return;

    setInputError("");
    setInput("");
    await handleSend(cleanText);
  };

  const handleStarterClick = (text) => {
    if (isLoading) return;
    setInput(text);
    window.setTimeout(() => {
      sendMessage(text);
    }, 120);
  };

  const handleSend = async (text) => {
    const cleanText = text.trim();
    if (!cleanText || isLoading) return;

    const loadingId = getMessageId("loading");
    setLastQuestion(cleanText);
    setResultData(null);
    setMessages((prev) => [
      ...prev,
      { id: getMessageId("user"), sender: "user", text: cleanText },
      { id: loadingId, sender: "bot", text: "Analyzing your issue", loading: true },
    ]);
    setIsLoading(true);

    try {
      const data = await analyzeProblem(cleanText, sessionId, language);
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      const shortSummary = getShortSummary(data);
      const fullResponse = {
        category: data.category || "unknown",
        subcategory: data.subcategory || "unknown",
        response: data.response || "",
        summary: data.summary || "",
        rights: toList(data.rights),
        steps: toList(data.steps),
        documents: toList(data.documents),
        locations: toList(data.locations),
        nextActions: toList(data.next_actions),
        report: data.report || null,
        stage: data.stage || "ready",
        location_note: data.location_note || "",
      };

      const questionText = data.question || "";
      const hasFinalResult = Boolean(data.summary);

      setResultData(hasFinalResult ? fullResponse : null);
      setAwaitingMoreDetails(Boolean(questionText) && !hasFinalResult);
      setCurrentFollowUpQuestion(Boolean(questionText) && !hasFinalResult ? questionText : "");
      setMessages((prev) =>
        prev.map((message) =>
          message.id === loadingId
            ? {
                id: getMessageId("bot"),
                sender: "bot",
                text: questionText || data.message || shortSummary,
              }
            : message,
        ),
      );
    } catch (err) {
      console.error(err);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === loadingId
            ? {
                id: getMessageId("bot-error"),
                sender: "bot",
                text: "Sorry, I could not reach the server. Please try again.",
              }
            : message,
        ),
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateDocument = async () => {
    if (!resultData || !resultData.report || isGeneratingDocument) return;

    setIsGeneratingDocument(true);
    try {
      await generateDocument({
        report: resultData.report,
      });
    } catch (error) {
      console.error(error);
    } finally {
      setIsGeneratingDocument(false);
    }
  };

  const handleViewLocations = () => {
    document.getElementById("nearby-offices")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const handleAskNextQuestion = async () => {
    if (!sessionId || isLoading) return;

    const loadingId = getMessageId("loading");
    setMessages((prev) => [
      ...prev,
      { id: loadingId, sender: "bot", text: "Getting the next question", loading: true },
    ]);
    setIsLoading(true);

    try {
      const data = await requestNextQuestion(sessionId);
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      const questionText = data.question || data.message || "Please continue with more details.";
      setCurrentFollowUpQuestion(data.question ? questionText : "");
      setAwaitingMoreDetails(Boolean(data.question));
      setMessages((prev) =>
        prev.map((message) =>
          message.id === loadingId
            ? { id: getMessageId("bot"), sender: "bot", text: questionText }
            : message,
        ),
      );
    } catch (error) {
      console.error(error);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === loadingId
            ? { id: getMessageId("bot-error"), sender: "bot", text: "Sorry, I could not fetch the next question." }
            : message,
        ),
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!resultData || resultData.stage !== "ready" || isGeneratingReport) return;

    setIsGeneratingReport(true);
    try {
      const data = await generateLegalReport(sessionId, "");
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      if (data.ok === false) {
        setMessages((prev) => [
          ...prev,
          { id: getMessageId("bot"), sender: "bot", text: data.message || "The report is not ready yet." },
        ]);
        if (data.follow_up) {
          setAwaitingMoreDetails(true);
          setCurrentFollowUpQuestion(data.question || "");
        }
        return;
      }

      setResultData((current) => {
        if (!current) return current;
        return {
          ...current,
          report: data.report || null,
          locations: toList(data.locations),
          location_note: data.location_note || current.location_note || "",
          summary: data.summary || current.summary,
          response: data.response || current.response,
        };
      });
    } catch (error) {
      console.error(error);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const handleAskAnother = () => {
    setInput("");
    setInputError("");
    setAwaitingMoreDetails(false);
    setCurrentFollowUpQuestion("");
    setResultData(null);
    setSessionId(createSessionId());
  };

  return (
    <div className="site-shell" data-theme={theme} onPointerMove={handlePointerMove}>
      <header className="site-header">
        <a className="brand" href="#home" aria-label="LegalEase AI home">
          <span className="brand-mark">L</span>
          <span>LegalEase AI</span>
        </a>
        <nav className="nav-links" aria-label="Primary navigation">
          <a href="#home">Home</a>
          <a href="#assistant">Legal Assistant</a>
          <a href="#about">About</a>
        </nav>
        <button
          className="theme-toggle"
          type="button"
          onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
        >
          <span className={theme === "dark" ? "active" : ""}>Dark</span>
          <span className={theme === "light" ? "active" : ""}>Light</span>
        </button>
      </header>

      <main>
        <section className="hero-section" id="home">
          <div className="hero-copy">
            <p className="section-kicker">Indian law, simplified</p>
            <h1>Legal Assistance Simplified with AI</h1>
            <p className="hero-text">
              LegalEase AI helps you understand legal issues, nearby support options,
              and common Indian legal processes in plain language.
            </p>
            <div className="hero-actions">
              <a className="primary-link" href="#assistant">Start Legal Chat</a>
              <a className="secondary-link" href="#about">Learn More</a>
            </div>
          </div>
          <div className="hero-visual" aria-hidden="true">
            <img src={heroImage} alt="" />
            <div className="visual-card top-card">Rights</div>
            <div className="visual-card bottom-card">Guidance</div>
          </div>
        </section>

        <section className="content-section" id="about">
          <div className="section-heading">
            <p className="section-kicker">How LegalEase AI can help you</p>
            <h2>Practical assistance for everyday legal questions</h2>
          </div>
          <div className="help-grid">
            {helpCards.map((card) => (
              <article className="help-card" key={card.title}>
                <span className="help-icon">{card.icon}</span>
                <h3>{card.title}</h3>
                <p>{card.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="content-section topic-section">
          <div className="section-heading">
            <p className="section-kicker">Legal topics we cover</p>
            <h2>Information across key areas of Indian law</h2>
          </div>
          <div className="topic-grid">
            {topics.map(([title, text]) => (
              <article className="topic-card" key={title}>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="assistant-section" id="assistant">
          <div className="assistant-dashboard">
            <div className="assistant-intro">
            <p className="section-kicker">Legal Assistant</p>
            <h2>Ask your question</h2>
            <p>
              Describe your situation and choose a language. The assistant will
              respond with useful legal information and relevant locations when
              available.
            </p>
            <ul className="feature-list" aria-label="LegalEase AI benefits">
              <li><span>OK</span> Know your legal rights</li>
              <li><span>OK</span> Get step-by-step guidance</li>
              <li><span>OK</span> Generate complaint letters instantly</li>
            </ul>
            <div className="prompt-row" aria-label="Example legal questions">
              {samplePrompts.map((prompt) => (
                <button
                  className="prompt-chip"
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  disabled={isLoading}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          <section className="chat-panel" aria-label="LegalEase AI legal chat">
            <header className="chat-header">
              <div>
                <p className="section-kicker">AI Legal Guidance Assistant</p>
                <h2>LegalEase AI Chat</h2>
              </div>
              <LanguageSelector selected={language} setSelected={setLanguage} />
            </header>

            <ChatWindow
              messages={messages}
              starterSuggestions={starterSuggestions}
              onStarterClick={handleStarterClick}
              disabled={isLoading}
            />

            <InputBar
              value={input}
              onChange={(value) => {
                setInput(value);
                if (value.trim()) setInputError("");
              }}
              onSend={sendMessage}
              disabled={isLoading}
              error={inputError}
              placeholder={getInputPlaceholder(currentFollowUpQuestion)}
            />
            {awaitingMoreDetails && (
              <div className="result-actions">
                <button className="action-button" type="button" onClick={handleAskNextQuestion} disabled={isLoading}>
                  Ask Next Question
                </button>
                {currentFollowUpQuestion && <p>{currentFollowUpQuestion}</p>}
              </div>
            )}
          </section>

          {resultData && (
            <div ref={resultRef}>
              <ResultPanel
                summary={resultData.summary || resultData.response}
                rights={resultData.rights}
                steps={resultData.steps}
                documents={resultData.documents}
                locations={resultData.locations}
                nextActions={resultData.nextActions}
                locationNote={resultData.location_note}
                report={resultData.report}
                reportReady={true}
                onGenerateReport={handleGenerateReport}
                isGeneratingReport={isGeneratingReport}
                onGenerateDocument={handleGenerateDocument}
                isGeneratingDocument={isGeneratingDocument}
                onViewLocations={handleViewLocations}
                onAskAnother={handleAskAnother}
              />
            </div>
          )}
          </div>
        </section>

        <section className="cta-section">
          <h2>Ready to get legal assistance?</h2>
          <p>Start a conversation with LegalEase AI and get legal information you can understand.</p>
          <a className="primary-link" href="#assistant">Chat Now</a>
        </section>
      </main>

      <footer className="site-footer">
        <div>
          <h3>LegalEase AI</h3>
          <p>Your AI-powered legal assistant for Indian law information and guidance.</p>
        </div>
        <div>
          <h3>Quick Links</h3>
          <a href="#home">Home</a>
          <a href="#assistant">Legal Assistant</a>
          <a href="#about">About</a>
        </div>
        <div>
          <h3>Disclaimer</h3>
          <p>
            LegalEase AI provides educational legal information, not legal advice.
            For specific concerns, consult a qualified legal professional in India.
          </p>
        </div>
      </footer>

    </div>
  );
};

export default App;
