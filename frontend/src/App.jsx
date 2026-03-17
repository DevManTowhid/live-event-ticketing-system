import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'; // We will use React Router for navigation
import Home from './pages/Home';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        {/* We will add the /login route here next! */}
      </Routes>
    </Router>
  );
}

export default App;