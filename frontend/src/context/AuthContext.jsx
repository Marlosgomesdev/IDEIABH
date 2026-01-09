import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return context;
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  // Configurar axios para incluir token em todas as requisições
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      verifyToken();
    } else {
      setLoading(false);
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Token inválido:', error);
      logout();
    }
  };

  const login = async (email, senha) => {
    try {
      // FastAPI OAuth2PasswordRequestForm espera username e password
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', senha);

      const response = await axios.post(`${API}/auth/login`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user)); // Salvar dados do usuário
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      console.error('Erro no login:', error);
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Erro ao fazer login' 
      };
    }
  };

  const register = async (nome, email, senha) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        nome,
        email,
        senha,
        role: 'Atendimento'
      });

      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      console.error('Erro no registro:', error);
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Erro ao registrar' 
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    if (user.role === 'Administrador') return true;
    return user.permissoes?.[permission] || false;
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    hasPermission,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'Administrador'
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
