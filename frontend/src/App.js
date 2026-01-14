import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import DashboardNovo from './pages/DashboardNovo';
import Contratos from './pages/Contratos';
import Projetos from './pages/Projetos';
import TarefasLista from './pages/TarefasLista';
import AdminUsers from './pages/AdminUsers';
import './App.css';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<DashboardNovo />} />
          <Route path="/contratos" element={<Contratos />} />
          <Route path="/projetos" element={<Projetos />} />
          <Route path="/tarefas" element={<TarefasLista />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;