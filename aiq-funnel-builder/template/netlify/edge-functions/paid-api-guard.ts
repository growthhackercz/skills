async function paidApiGuard(
  _request: Request,
  context: { next: () => Promise<Response> }
) {
  return context.next();
}

export default paidApiGuard;

export const config = {
  path: ["/api/submit", "/api/personalize"],
  method: "POST",
  rateLimit: {
    windowSize: 180,
    windowLimit: 6,
    aggregateBy: ["ip", "domain"],
  },
};
