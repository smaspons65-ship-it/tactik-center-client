/**
 * Shared types for the TACTIK 6.3 Chaser Engine.
 * Mirrors the contract in TACTIK_6_3_CHASER_ENGINE.docx section 11 (API del módulo 6.3).
 */

export type PipelineState =
  | "human_pause"
  | "thinking"
  | "thinking_longer"
  | "searching"
  | string;

export interface Avatar {
  tone?: string;
  domain?: string;
  vocabulary?: string[];
  creativityTarget?: number;
}

export interface Turn {
  text: string;
  metadata?: Record<string, unknown>;
}

export interface ChaserTrace {
  step: string;
  changed: boolean;
  notes?: string;
}
