import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
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
    <div className="login-container">
      <div className="login-left">
        <div className="login-left-overlay">
          <div className="login-brand">
            <h1 className="brand-title">IDEIABH</h1>
            <p className="brand-subtitle">Motor Inteligente de Gestão Operacional</p>
            <p className="brand-description">Workflow e Governança de Projetos</p>
          </div>
        </div>
      </div>

      <div className="login-right">
        <div className="login-card">
          <div className="login-header">
            <h2 className="login-title">Bem-vindo de volta</h2>
            <p className="login-subtitle">Faça login para acessar o sistema</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <Label htmlFor="email" className="form-label">E-mail</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="form-input"
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <Label htmlFor="senha" className="form-label">Senha</Label>
              <Input
                id="senha"
                type="password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                className="form-input"
                required
                disabled={loading}
              />
            </div>

            <Button type="submit" className="login-button" disabled={loading}>
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>

          <div className="login-footer">
            <p className="register-link">
              Não tem uma conta?{' '}
              <Link to="/register" className="register-link-text">
                Cadastre-se
              </Link>
            </p>
          </div>
        </div>

        <div className="emergent-badge">
          <a 
            href="https://app.emergent.sh/?utm_source=emergent-badge" 
            target="_blank" 
            rel="noopener noreferrer"
            className="badge-link"
          >
            <img 
              src="https://avatars.githubusercontent.com/in/1201222?s=120&u=2686cf91179bbafbc7a71bfbc43004cf9ae1acea&v=4" 
              alt="Emergent" 
              className="badge-icon"
            />
            <span className="badge-text">Made with Emergent</span>
          </a>
        </div>
      </div>
    </div>
  );
};

export default Login;