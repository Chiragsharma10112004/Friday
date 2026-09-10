"use client";

import { useState, useEffect, useCallback, useRef } from "react";

const VOICE_PREF_KEY = "friday_voice_enabled";

/**
 * Strip raw markdown, code blocks, URLs, and table artifacts so speech is natural and clean.
 */
export function sanitizeTextForSpeech(text: string): string {
  if (!text) return "";

  let cleaned = text;

  // 1. Remove code blocks ```...```
  cleaned = cleaned.replace(/```[\s\S]*?```/g, " [code snippet omitted] ");

  // 2. Remove inline code `...`
  cleaned = cleaned.replace(/`([^`]+)`/g, "$1");

  // 3. Remove URLs
  cleaned = cleaned.replace(/https?:\/\/\S+/g, "");

  // 4. Transform markdown links [Text](url) -> Text
  cleaned = cleaned.replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1");

  // 5. Remove headers, bullet points, blockquotes, horizontal rules
  cleaned = cleaned.replace(/^#+\s+/gm, "");
  cleaned = cleaned.replace(/^[\*\-\+]\s+/gm, "");
  cleaned = cleaned.replace(/^\>\s+/gm, "");
  cleaned = cleaned.replace(/^\s*[-*_]{3,}\s*$/gm, "");

  // 6. Remove bold/italic markers
  cleaned = cleaned.replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, "$1");

  // 7. Remove table separators and borders
  cleaned = cleaned.replace(/\|/g, " ");

  // 8. Normalize whitespace
  cleaned = cleaned.replace(/\s+/g, " ").trim();

  // Cap speech length to prevent runaway speaking on huge outputs (e.g. 500 words max)
  const words = cleaned.split(" ");
  if (words.length > 250) {
    cleaned = words.slice(0, 250).join(" ") + "... Summary completed.";
  }

  return cleaned;
}

export class FridayVoiceEngine {
  private static instance: FridayVoiceEngine;
  private isSpeaking: boolean = false;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private listeners: Set<(speaking: boolean) => void> = new Set();
  private lastSpokenText: string = "";

  private constructor() {}

  public static getInstance(): FridayVoiceEngine {
    if (!FridayVoiceEngine.instance) {
      FridayVoiceEngine.instance = new FridayVoiceEngine();
    }
    return FridayVoiceEngine.instance;
  }

  public subscribe(listener: (speaking: boolean) => void): () => void {
    this.listeners.add(listener);
    listener(this.isSpeaking);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((l) => l(this.isSpeaking));
  }

  public isVoiceSupported(): boolean {
    return typeof window !== "undefined" && "speechSynthesis" in window;
  }

  public getVoiceEnabled(): boolean {
    if (typeof window === "undefined") return true;
    const stored = localStorage.getItem(VOICE_PREF_KEY);
    // Defaults to true (ON) for new users/sessions
    return stored === null ? true : stored === "true";
  }

  public setVoiceEnabled(enabled: boolean) {
    if (typeof window === "undefined") return;
    localStorage.setItem(VOICE_PREF_KEY, String(enabled));
    if (!enabled) {
      this.stop();
    }
  }

  public speak(text: string) {
    if (!this.isVoiceSupported() || !this.getVoiceEnabled()) return;

    const speechText = sanitizeTextForSpeech(text);
    if (!speechText || speechText === this.lastSpokenText) return;

    this.stop();

    try {
      const utterance = new SpeechSynthesisUtterance(speechText);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;

      // Select a high quality English voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (v.name.includes("Natural") ||
            v.name.includes("Google") ||
            v.name.includes("Samantha") ||
            v.name.includes("David") ||
            v.name.includes("Zira"))
      ) || voices.find((v) => v.lang.startsWith("en"));

      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      utterance.onstart = () => {
        this.isSpeaking = true;
        this.notify();
      };

      utterance.onend = () => {
        this.isSpeaking = false;
        this.currentUtterance = null;
        this.notify();
      };

      utterance.onerror = (e) => {
        // Gracefully ignore user cancellations / interruptions
        if (e.error !== "canceled" && e.error !== "interrupted") {
          console.debug("Speech synthesis notice:", e.error);
        }
        this.isSpeaking = false;
        this.currentUtterance = null;
        this.notify();
      };

      this.lastSpokenText = speechText;
      this.currentUtterance = utterance;
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.debug("Voice speech could not start:", err);
      this.isSpeaking = false;
      this.notify();
    }
  }

  public stop() {
    if (!this.isVoiceSupported()) return;
    try {
      window.speechSynthesis.cancel();
    } catch {
      // Ignore cleanup error
    }
    this.isSpeaking = false;
    this.currentUtterance = null;
    this.notify();
  }
}

export const fridayVoice = FridayVoiceEngine.getInstance();

export function useFridayVoice() {
  const [isVoiceEnabled, setIsVoiceEnabledState] = useState<boolean>(true);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    setIsVoiceEnabledState(fridayVoice.getVoiceEnabled());

    const unsubscribe = fridayVoice.subscribe((speaking) => {
      if (mountedRef.current) {
        setIsSpeaking(speaking);
      }
    });

    return () => {
      mountedRef.current = false;
      unsubscribe();
    };
  }, []);

  const toggleVoice = useCallback(() => {
    const nextState = !isVoiceEnabled;
    setIsVoiceEnabledState(nextState);
    fridayVoice.setVoiceEnabled(nextState);
  }, [isVoiceEnabled]);

  const speak = useCallback((text: string) => {
    fridayVoice.speak(text);
  }, []);

  const stop = useCallback(() => {
    fridayVoice.stop();
  }, []);

  return {
    isVoiceEnabled,
    isSpeaking,
    toggleVoice,
    speak,
    stop,
  };
}

