import { describe, expect, it } from 'vitest';
import {
  applyInertia,
  applyScrollInertia,
  clampScrollDelta,
  clampScrollSensitivity,
  clampSensitivity,
  classifyGesture,
  computeScrollDelta,
  isTwoFingerScrollGesture
} from '../../src/laptop_remote/static/js/trackpad-logic.js';

describe('applyInertia', () => {
  it('applies decay to velocity', () => {
    expect(applyInertia(10, 0.82)).toBeCloseTo(8.2);
  });

  it('preserves the direction of velocity', () => {
    expect(applyInertia(-10, 0.82)).toBeCloseTo(-8.2);
  });

  it('returns 0 when initial velocity is 0', () => {
    expect(applyInertia(0, 0.82)).toBe(0);
  });
});

describe('clampSensitivity', () => {
  it('clamps values below the minimum', () => {
    expect(clampSensitivity(0.1)).toBe(0.5);
  });

  it('clamps values above the maximum', () => {
    expect(clampSensitivity(5)).toBe(4.0);
  });

  it('keeps values inside the range unchanged', () => {
    expect(clampSensitivity(1.2)).toBe(1.2);
  });

  it('respects custom min and max parameters', () => {
    expect(clampSensitivity(0.2, 0.1, 2.0)).toBe(0.2);
    expect(clampSensitivity(0.05, 0.1, 2.0)).toBe(0.1);
    expect(clampSensitivity(3.0, 0.1, 2.0)).toBe(2.0);
  });
});

describe('clampScrollSensitivity', () => {
  it('clamps values below min', () => {
    expect(clampScrollSensitivity(0.05)).toBe(0.2);
  });

  it('clamps values above max', () => {
    expect(clampScrollSensitivity(5.0)).toBe(3.0);
  });

  it('preserves valid values', () => {
    expect(clampScrollSensitivity(1.4)).toBe(1.4);
  });
});

describe('computeScrollDelta', () => {
  it('calibrates touch pixels into reasonable scroll units with natural direction', () => {
    // 36px swipe divided by 18 = 2.0 clicks
    expect(computeScrollDelta(36, 1.0, 'natural')).toBeCloseTo(2.0);
  });

  it('inverts scroll delta when inverted direction is requested', () => {
    expect(computeScrollDelta(36, 1.0, 'inverted')).toBeCloseTo(-2.0);
  });

  it('scales delta linearly with scrollSensitivity', () => {
    expect(computeScrollDelta(36, 1.5, 'natural')).toBeCloseTo(3.0);
    expect(computeScrollDelta(36, 0.5, 'natural')).toBeCloseTo(1.0);
  });
});

describe('clampScrollDelta', () => {
  it('clamps values exceeding maxPerFrame', () => {
    expect(clampScrollDelta(10, 4.0)).toBe(4.0);
    expect(clampScrollDelta(-10, 4.0)).toBe(-4.0);
  });

  it('leaves values within bounds intact', () => {
    expect(clampScrollDelta(2.5, 4.0)).toBe(2.5);
  });
});

describe('applyScrollInertia', () => {
  it('applies fast decay and drops to 0 below threshold', () => {
    // 1.0 * 0.70 = 0.70
    expect(applyScrollInertia(1.0, 0.70, 0.4)).toBeCloseTo(0.70);
    // 0.5 * 0.70 = 0.35, which is < 0.4 minVelocity -> drops to 0
    expect(applyScrollInertia(0.5, 0.70, 0.4)).toBe(0);
  });
});

describe('isTwoFingerScrollGesture', () => {
  it('returns false when movement is below deadzone threshold', () => {
    const start = [{ x: 100, y: 100 }, { x: 200, y: 100 }];
    const current = [{ x: 101, y: 102 }, { x: 201, y: 102 }];
    expect(isTwoFingerScrollGesture(current, start, 6)).toBe(false);
  });

  it('returns true when movement exceeds deadzone threshold', () => {
    const start = [{ x: 100, y: 100 }, { x: 200, y: 100 }];
    const current = [{ x: 100, y: 115 }, { x: 200, y: 115 }];
    expect(isTwoFingerScrollGesture(current, start, 6)).toBe(true);
  });

  it('returns false for invalid touches', () => {
    expect(isTwoFingerScrollGesture([], [], 6)).toBe(false);
    expect(isTwoFingerScrollGesture([{ x: 1, y: 1 }], [{ x: 1, y: 1 }], 6)).toBe(false);
  });
});

describe('classifyGesture', () => {
  it('detects two-finger movement as scroll', () => {
    const previous = [
      { x: 100, y: 100 },
      { x: 200, y: 100 }
    ];

    const current = [
      { x: 100, y: 120 },
      { x: 200, y: 120 }
    ];

    expect(classifyGesture(previous, current)).toBe('scroll');
  });

  it('detects movement above the threshold', () => {
    const previous = [{ x: 100, y: 100 }];
    const current = [{ x: 104, y: 100 }];

    expect(classifyGesture(previous, current, 4)).toBe('move');
  });

  it('detects movement within the threshold as tap', () => {
    const previous = [{ x: 100, y: 100 }];
    const current = [{ x: 101, y: 100 }];

    expect(classifyGesture(previous, current, 1)).toBe('tap');
  });

  it('treats movement at the threshold as tap', () => {
    const previous = [{ x: 100, y: 100 }];
    const current = [{ x: 102, y: 100 }];

    expect(classifyGesture(previous, current, 2)).toBe('tap');
  });

  it('handles empty touch lists gracefully', () => {
    expect(classifyGesture([], [])).toBe('tap');
  });
});