export function calculateDistance(location1: number[], location2: number[]) {
  // Calculate distance between two points using Pythagorean theorem
  const distance = Math.sqrt(
    (location1[0] - location2[0]) * (location1[0] - location2[0]) +
      (location1[1] - location2[1]) * (location1[1] - location2[1])
  );
  // Round to two decimal places
  return Math.round(distance * 100) / 100;
}
