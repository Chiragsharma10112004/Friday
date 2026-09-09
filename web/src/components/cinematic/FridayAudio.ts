/**
 * FRIDAY Web Audio Synthesizer Engine
 * Procedural, reactive, zero-asset audio architecture for cinematic 3D experience.
 */

class FridayAudioEngine {
  private ctx: AudioContext | null = null;
  private isMuted: boolean = true;
  private isInitialized: boolean = false;

  // Sound nodes
  private masterGain: GainNode | null = null;
  private droneGain: GainNode | null = null;
  private droneOsc1: OscillatorNode | null = null;
  private droneOsc2: OscillatorNode | null = null;
  private droneFilter: BiquadFilterNode | null = null;

  private awakenGain: GainNode | null = null;
  private awakenOsc: OscillatorNode | null = null;
  private awakenFilter: BiquadFilterNode | null = null;

  private pulseGain: GainNode | null = null;
  private pulseInterval: number | null = null;

  // Analyser for UI visualizers
  public analyser: AnalyserNode | null = null;

  public init() {
    if (this.isInitialized || typeof window === "undefined") return;

    try {
      const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioContextClass();

      // Master output
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(this.isMuted ? 0 : 0.6, this.ctx.currentTime);

      // Analyser for HUD visualizer
      this.analyser = this.ctx.createAnalyser();
      this.analyser.fftSize = 64;
      this.masterGain.connect(this.analyser);
      this.analyser.connect(this.ctx.destination);

      this.setupAmbientDrone();
      this.setupAwakenSynth();
      this.setupDataPulseSynth();

      this.isInitialized = true;
    } catch (e) {
      console.warn("Web Audio API not supported or initialized:", e);
    }
  }

  private setupAmbientDrone() {
    if (!this.ctx || !this.masterGain) return;

    // Deep sub-bass drone (45Hz + 90Hz harmonic)
    this.droneOsc1 = this.ctx.createOscillator();
    this.droneOsc1.type = "sine";
    this.droneOsc1.frequency.setValueAtTime(45, this.ctx.currentTime);

    this.droneOsc2 = this.ctx.createOscillator();
    this.droneOsc2.type = "triangle";
    this.droneOsc2.frequency.setValueAtTime(90.5, this.ctx.currentTime);

    this.droneFilter = this.ctx.createBiquadFilter();
    this.droneFilter.type = "lowpass";
    this.droneFilter.frequency.setValueAtTime(140, this.ctx.currentTime);
    this.droneFilter.Q.setValueAtTime(3.5, this.ctx.currentTime);

    this.droneGain = this.ctx.createGain();
    this.droneGain.gain.setValueAtTime(0.25, this.ctx.currentTime);

    this.droneOsc1.connect(this.droneFilter);
    this.droneOsc2.connect(this.droneFilter);
    this.droneFilter.connect(this.droneGain);
    this.droneGain.connect(this.masterGain);

    this.droneOsc1.start();
    this.droneOsc2.start();
  }

  private setupAwakenSynth() {
    if (!this.ctx || !this.masterGain) return;

    // Harmonic riser for awakening state
    this.awakenOsc = this.ctx.createOscillator();
    this.awakenOsc.type = "sawtooth";
    this.awakenOsc.frequency.setValueAtTime(110, this.ctx.currentTime);

    this.awakenFilter = this.ctx.createBiquadFilter();
    this.awakenFilter.type = "bandpass";
    this.awakenFilter.frequency.setValueAtTime(220, this.ctx.currentTime);
    this.awakenFilter.Q.setValueAtTime(4.0, this.ctx.currentTime);

    this.awakenGain = this.ctx.createGain();
    this.awakenGain.gain.setValueAtTime(0.0, this.ctx.currentTime);

    this.awakenOsc.connect(this.awakenFilter);
    this.awakenFilter.connect(this.awakenGain);
    this.awakenGain.connect(this.masterGain);

    this.awakenOsc.start();
  }

  private setupDataPulseSynth() {
    if (!this.ctx || !this.masterGain) return;

    this.pulseGain = this.ctx.createGain();
    this.pulseGain.gain.setValueAtTime(0.0, this.ctx.currentTime);
    this.pulseGain.connect(this.masterGain);
  }

  /**
   * Modulate audio parameters dynamically based on scroll position (0.0 -> 1.0)
   */
  public updateScroll(progress: number, velocity: number = 0) {
    if (!this.ctx || this.isMuted) return;

    const t = this.ctx.currentTime;
    const smoothTime = 0.1;

    // Scene 1 -> Boot (0.0 - 0.3)
    // Scene 2 -> Awaken (0.3 - 0.6)
    // Scene 3 -> Repository (0.6 - 1.0)

    if (this.droneFilter && this.droneGain) {
      // Open up drone filter as user travels deeper
      const droneFreq = 120 + progress * 240 + Math.min(Math.abs(velocity) * 400, 300);
      this.droneFilter.frequency.setTargetAtTime(droneFreq, t, smoothTime);
      this.droneGain.gain.setTargetAtTime(0.25 - progress * 0.1, t, smoothTime);
    }

    if (this.awakenGain && this.awakenFilter && this.awakenOsc) {
      // Scene 2 Awakening peak
      const awakenIntensity = Math.sin(Math.max(0, Math.min(1, (progress - 0.25) / 0.35)) * Math.PI);
      this.awakenGain.gain.setTargetAtTime(awakenIntensity * 0.2, t, smoothTime);

      const awakenFreq = 180 + progress * 480;
      this.awakenFilter.frequency.setTargetAtTime(awakenFreq, t, smoothTime);
      this.awakenOsc.frequency.setTargetAtTime(110 + progress * 110, t, smoothTime);
    }

    // Trigger random digital blips in repository phase (Scene 3)
    if (progress > 0.55 && Math.random() < 0.15) {
      this.triggerDataBlip(1200 + Math.random() * 2400, 0.04);
    }
  }

  /**
   * Play a delicate digital data blip
   */
  public triggerDataBlip(freq: number = 2200, duration: number = 0.05) {
    if (!this.ctx || !this.masterGain || this.isMuted) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(freq * 0.6, this.ctx.currentTime + duration);

      gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch {
      // Audio node cleanup
    }
  }

  /**
   * UI Click Micro-Sound
   */
  public playClick(pitch: number = 880) {
    if (!this.ctx || !this.masterGain || this.isMuted) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = "triangle";
      osc.frequency.setValueAtTime(pitch, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(pitch * 1.5, this.ctx.currentTime + 0.03);

      gain.gain.setValueAtTime(0.06, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.03);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.03);
    } catch {
      // Audio node cleanup
    }
  }

  /**
   * Resume audio context on user gesture
   */
  public async resume() {
    if (!this.ctx) {
      this.init();
    }
    if (this.ctx && this.ctx.state === "suspended") {
      await this.ctx.resume();
    }
  }

  /**
   * Toggle Mute State
   */
  public toggleMute(): boolean {
    this.resume();
    this.isMuted = !this.isMuted;

    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setTargetAtTime(this.isMuted ? 0.0 : 0.6, this.ctx.currentTime, 0.1);
    }

    if (!this.isMuted) {
      this.playClick(1200);
    }

    return this.isMuted;
  }

  public getMuted(): boolean {
    return this.isMuted;
  }

  public getAnalyserData(): Uint8Array {
    if (!this.analyser) return new Uint8Array(32);
    const data = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(data);
    return data;
  }
}

export const fridayAudio = new FridayAudioEngine();

