import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { Mail, Lock, ArrowRight, Sparkles } from 'lucide-react';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await login(email, senha);
    
    if (result.success) {
      toast({ title: 'Login realizado com sucesso!' });
      navigate('/dashboard');
    } else {
      toast({ 
        title: 'Erro ao fazer login', 
        description: result.message,
        variant: 'destructive' 
      });
    }
    
    setLoading(false);
  };

  return (
    <div className="login-wrapper">
      {/* Fundo com gradiente animado */}
      <div className="login-background">
        <div className="gradient-circle circle-1"></div>
        <div className="gradient-circle circle-2"></div>
        <div className="gradient-circle circle-3"></div>
      </div>

      {/* Container principal */}
      <div className="login-content">
        {/* Logo e título */}
        <div className="login-header">
          <div className="logo-container">
            <Sparkles className="logo-icon" />
            <h1 className="logo-text">IDEIABH</h1>
          </div>
          <p className="welcome-text">Sistema de Gestão Operacional</p>
          <p className="welcome-subtitle">Faça login para continuar</p>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <Label htmlFor="email" className="form-label">
              Email
            </Label>
            <div className="input-wrapper">
              <Mail className="input-icon" size={18} />
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="form-input"
                data-testid="email-input"
              />
            </div>
          </div>

          <div className="form-group">
            <Label htmlFor="senha" className="form-label">
              Senha
            </Label>
            <div className="input-wrapper">
              <Lock className="input-icon" size={18} />
              <Input
                id="senha"
                type="password"
                placeholder="••••••••"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
                className="form-input"
                data-testid="password-input"
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="submit-button"
            data-testid="login-button"
          >
            {loading ? (
              <span className="loading-spinner">Entrando...</span>
            ) : (
              <>
                <span>Entrar</span>
                <ArrowRight className="button-icon" size={18} />
              </>
            )}
          </Button>
        </form>

        {/* Link de registro */}
        <div className="login-footer">
          <p className="footer-text">
            Não tem uma conta?
            <Link to="/register" className="footer-link">
              Criar conta
            </Link>
          </p>
        </div>

        {/* Credenciais de demonstração */}
        <div className="demo-credentials">
          <p className="demo-title">Credenciais de demonstração:</p>
          <div className="demo-info">
            <span className="demo-label">Email:</span>
            <code className="demo-value">admin@ideiabh.com</code>
          </div>
          <div className="demo-info">
            <span className="demo-label">Senha:</span>
            <code className="demo-value">admin123</code>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;