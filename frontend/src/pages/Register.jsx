import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import './Login.css';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert('As senhas não correspondem');
      return;
    }
    console.log('Register attempt:', { name, email, password });
    // TODO: Implement register logic
  };

  return (
    <div className="login-container">
      {/* Left Side - Brand Section */}
      <div className="login-left">
        <div className="login-left-overlay">
          <div className="login-brand">
            <h1 className="brand-title">IDEIABH</h1>
            <p className="brand-subtitle">Motor Inteligente de Gestão Operacional</p>
            <p className="brand-description">Workflow e Governança de Projetos</p>
          </div>
        </div>
      </div>

      {/* Right Side - Register Form */}
      <div className="login-right">
        <div className="login-card">
          <div className="login-header">
            <h2 className="login-title">Criar uma conta</h2>
            <p className="login-subtitle">Preencha os dados para se cadastrar</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <Label htmlFor="name" className="form-label">Nome completo</Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <Label htmlFor="email" className="form-label">E-mail</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <Label htmlFor="password" className="form-label">Senha</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <Label htmlFor="confirmPassword" className="form-label">Confirmar senha</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="form-input"
                required
              />
            </div>

            <Button type="submit" className="login-button">
              Cadastrar
            </Button>
          </form>

          <div className="login-footer">
            <p className="register-link">
              Já tem uma conta?{' '}
              <Link to="/" className="register-link-text">
                Faça login
              </Link>
            </p>
          </div>
        </div>

        {/* Emergent Badge */}
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

export default Register;