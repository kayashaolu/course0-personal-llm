// Small attribution link back to the course this starter repo comes from.
// This is not part of the app's own product surface, so if you're removing
// it, take all of it out cleanly: both marker-wrapped blocks in App.jsx (the
// import near the top, and the <BrandCredit /> render lower down), this
// file, the frontend/assets/systemthinkinglab-mark.png image it points at,
// the matching test block in tests/App.test.jsx, and (if one was added) the
// .brand-credit rule in index.css.
function BrandCredit() {
  return (
    <a
      href="https://systemthinkinglab.ai/course-0.html"
      target="_blank"
      rel="noopener"
      className="brand-credit"
    >
      <img src="assets/systemthinkinglab-mark.png" alt="" width="16" height="16" />
      Built for Systems Thinking Lab's Course 0
    </a>
  );
}

export default BrandCredit;
