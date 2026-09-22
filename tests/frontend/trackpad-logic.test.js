import { describe, expect, it } from 'vitest';
import {
  applyInertia,
  clampSensitivity,
  classifyGesture
} from '../../src/laptop_remote/static/js/trackpad-logic.js';

describe('applyInertia', () => {
  it('applies decay to velocity', () => {
    expect(applyInertia(10, 0.82)).toBeCloseTo(8.2);
  });

  it('preserves the direction of velocity', () => {
    expect(applyInertia(-10, 0.82)).toBeCloseTo(-8.2);
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
});