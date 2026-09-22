export function applyInertia(velocity, decay) {
  return velocity * decay;
}

export function clampSensitivity(value, min = 0.5, max = 4.0) {
  return Math.min(max, Math.max(min, value));
}

// export function classifyGesture(prevPoints, currPoints, movementThreshold = 2) {
//   if (currPoints.length === 2) {
//     return 'scroll';
//   }

//   if (currPoints.length === 1 && prevPoints.length === 1) {
//     const dx = currPoints[0].x - prevPoints[0].x;
//     const dy = currPoints[0].y - prevPoints[0].y;
//     const distance = Math.sqrt(dx * dx + dy * dy);

//     return distance > movementThreshold ? 'move' : 'tap';
//   }

//   return 'tap';
// }
export function classifyGesture(
  prevPoints,
  currPoints,
  totalMovement = 0,
  movementThreshold = 2
) {
  if (currPoints.length === 2) {
    return 'scroll';
  }

  if (currPoints.length === 1 && prevPoints.length === 1) {
    return totalMovement > movementThreshold ? 'move' : 'tap';
  }

  return 'tap';
}

if (typeof window !== 'undefined') {
  window.trackpadLogic = {
    applyInertia,
    clampSensitivity,
    classifyGesture
  };
}