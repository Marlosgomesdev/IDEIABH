import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { UserPlus, Edit, Trash2, Shield, Users } from 'lucide-react';
import './AdminUsers.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const { toast } = useToast();

  const [newUser, setNewUser] = useState({
    nome: '',
    email: '',
    senha: '',
    role: 'Atendimento'
  });

  const roles = [
    'Administrador',
    'Atendimento',
    'Criação',
    'Pré-Produção',
    'Produção',
    'Revisão de Texto',
    'Cliente'
  ];

  const permissionGroups = {
    'Contratos': [
      { key: 'contratos_visualizar', label: 'Visualizar Contratos' },
      { key: 'contratos_criar', label: 'Criar Contratos' },
      { key: 'contratos_editar', label: 'Editar Contratos' },
      { key: 'contratos_excluir', label: 'Excluir Contratos' },
      { key: 'contratos_aprovar', label: 'Aprovar Contratos' },
      { key: 'contratos_finalizar', label: 'Finalizar Contratos' }
    ],
    'Projetos': [
      { key: 'projetos_visualizar', label: 'Visualizar Projetos' },
      { key: 'projetos_avancar', label: 'Avançar Etapas' },
      { key: 'projetos_mover_etapa', label: 'Mover Entre Etapas' }
    ],
    'Tarefas': [
      { key: 'tarefas_visualizar', label: 'Visualizar Tarefas' },
      { key: 'tarefas_criar', label: 'Criar Tarefas' },
      { key: 'tarefas_editar', label: 'Editar Tarefas' },
      { key: 'tarefas_concluir', label: 'Concluir Tarefas' },
      { key: 'tarefas_mover', label: 'Mover Tarefas (Kanban)' },
      { key: 'tarefas_excluir', label: 'Excluir Tarefas' }
    ],
    'Etapas do Workflow': [
      { key: 'etapa_lancamento', label: '1 - Lançamento' },
      { key: 'etapa_ativacao', label: '2 - Ativação' },
      { key: 'etapa_revisao', label: '3 - Revisão/Preparação' },
      { key: 'etapa_criacao_1_2', label: '4 - Criação (1ª/2ª)' },
      { key: 'etapa_conferencia', label: '5 - Conferência' },
      { key: 'etapa_ajuste_layout', label: '5.1 - Ajuste Layout' },
      { key: 'etapa_criacao_3_4', label: '6 - Criação (3ª/4ª)' },
      { key: 'etapa_aprovacao_final', label: '7 - Aprovação Final' },
      { key: 'etapa_planejamento_producao', label: '8 - Planejamento Produção' },
      { key: 'etapa_pre_producao', label: '9 - Pré-Produção' },
      { key: 'etapa_producao', label: '10 - Produção' },
      { key: 'etapa_qualidade', label: '11 - Qualidade' },
      { key: 'etapa_entrega', label: '12 - Entrega' },
      { key: 'etapa_pos_vendas', label: '13 - Pós-Vendas' }
    ],
    'Feedback e Interação': [
      { key: 'dar_feedback', label: 'Dar Feedback' },
      { key: 'ver_feedback', label: 'Ver Feedback' }
    ]
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const getToken = () => {
    return localStorage.getItem('token');
  };

  const fetchUsers = async () => {
    try {
      const token = getToken();
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      toast({
        title: 'Erro',
        description: error.response?.data?.detail || 'Erro ao carregar usuários',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    try {
      const token = getToken();
      await axios.post(`${API}/admin/users`, newUser, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast({
        title: 'Sucesso',
        description: 'Usuário criado com sucesso'
      });
      
      setShowCreateModal(false);
      setNewUser({ nome: '', email: '', senha: '', role: 'Atendimento' });
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Erro',
        description: error.response?.data?.detail || 'Erro ao criar usuário',
        variant: 'destructive'
      });
    }
  };

  const handleUpdatePermission = async (userId, permissionKey, value) => {
    try {
      const token = getToken();
      const user = users.find(u => u.id === userId);
      const updatedPermissions = { ...user.permissoes, [permissionKey]: value };
      
      await axios.put(`${API}/admin/users/${userId}`, 
        { permissoes: updatedPermissions },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Atualizar localmente
      setUsers(users.map(u => 
        u.id === userId 
          ? { ...u, permissoes: updatedPermissions }
          : u
      ));
      
      if (selectedUser && selectedUser.id === userId) {
        setSelectedUser({ ...selectedUser, permissoes: updatedPermissions });
      }
      
      toast({
        title: 'Sucesso',
        description: 'Permissão atualizada',
        duration: 2000
      });
    } catch (error) {
      toast({
        title: 'Erro',
        description: 'Erro ao atualizar permissão',
        variant: 'destructive'
      });
    }
  };

  const handleToggleUserStatus = async (userId, currentStatus) => {
    try {
      const token = getToken();
      await axios.put(`${API}/admin/users/${userId}`, 
        { ativo: !currentStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      fetchUsers();
      toast({
        title: 'Sucesso',
        description: `Usuário ${!currentStatus ? 'ativado' : 'desativado'}`
      });
    } catch (error) {
      toast({
        title: 'Erro',
        description: 'Erro ao atualizar status',
        variant: 'destructive'
      });
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Tem certeza que deseja excluir este usuário?')) return;
    
    try {
      const token = getToken();
      await axios.delete(`${API}/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchUsers();
      toast({
        title: 'Sucesso',
        description: 'Usuário excluído'
      });
    } catch (error) {
      toast({
        title: 'Erro',
        description: 'Erro ao excluir usuário',
        variant: 'destructive'
      });
    }
  };

  if (loading) {
    return <div className="admin-users-container"><p>Carregando...</p></div>;
  }

  return (
    <div className="admin-users-container" data-testid="admin-users-page">
      <div className="admin-users-header">
        <div>
          <h1 className="admin-users-title" data-testid="admin-users-title">
            <Users className="title-icon" />
            Gerenciamento de Usuários
          </h1>
          <p className="admin-users-subtitle">Crie usuários e gerencie suas permissões</p>
        </div>
        
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button data-testid="create-user-btn" className="create-user-btn">
              <UserPlus className="btn-icon" />
              Novo Usuário
            </Button>
          </DialogTrigger>
          <DialogContent className="create-user-modal">
            <DialogHeader>
              <DialogTitle>Criar Novo Usuário</DialogTitle>
              <DialogDescription>
                Preencha os dados do novo usuário. As permissões podem ser configuradas depois.
              </DialogDescription>
            </DialogHeader>
            
            <div className="form-group">
              <Label htmlFor="nome">Nome Completo</Label>
              <Input
                id="nome"
                data-testid="user-name-input"
                value={newUser.nome}
                onChange={(e) => setNewUser({...newUser, nome: e.target.value})}
                placeholder="Ex: João Silva"
              />
            </div>
            
            <div className="form-group">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                data-testid="user-email-input"
                value={newUser.email}
                onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                placeholder="Ex: joao@exemplo.com"
              />
            </div>
            
            <div className="form-group">
              <Label htmlFor="senha">Senha</Label>
              <Input
                id="senha"
                type="password"
                data-testid="user-password-input"
                value={newUser.senha}
                onChange={(e) => setNewUser({...newUser, senha: e.target.value})}
                placeholder="Mínimo 6 caracteres"
              />
            </div>
            
            <div className="form-group">
              <Label htmlFor="role">Função</Label>
              <Select value={newUser.role} onValueChange={(value) => setNewUser({...newUser, role: value})}>
                <SelectTrigger data-testid="user-role-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {roles.map(role => (
                    <SelectItem key={role} value={role}>{role}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="modal-actions">
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancelar
              </Button>
              <Button onClick={handleCreateUser} data-testid="submit-create-user">
                Criar Usuário
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="users-grid">
        {users.map(user => (
          <Card key={user.id} className="user-card" data-testid={`user-card-${user.id}`}>
            <CardHeader>
              <div className="user-card-header">
                <div>
                  <CardTitle className="user-name">{user.nome}</CardTitle>
                  <CardDescription>{user.email}</CardDescription>
                </div>
                <div className="user-actions">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        data-testid={`edit-permissions-${user.id}`}
                        onClick={() => setSelectedUser(user)}
                      >
                        <Shield className="btn-icon" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="permissions-modal">
                      <DialogHeader>
                        <DialogTitle>Permissões de {user.nome}</DialogTitle>
                        <DialogDescription>
                          Ative ou desative as capacidades deste usuário
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="permissions-content">
                        {Object.entries(permissionGroups).map(([groupName, permissions]) => (
                          <div key={groupName} className="permission-group">
                            <h4 className="permission-group-title">{groupName}</h4>
                            <div className="permission-list">
                              {permissions.map(perm => (
                                <div key={perm.key} className="permission-item">
                                  <div className="permission-info">
                                    <Label htmlFor={`${user.id}-${perm.key}`}>{perm.label}</Label>
                                  </div>
                                  <Switch
                                    id={`${user.id}-${perm.key}`}
                                    data-testid={`permission-${user.id}-${perm.key}`}
                                    checked={user.permissoes?.[perm.key] || false}
                                    onCheckedChange={(checked) => handleUpdatePermission(user.id, perm.key, checked)}
                                  />
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </DialogContent>
                  </Dialog>
                  
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => handleDeleteUser(user.id)}
                    data-testid={`delete-user-${user.id}`}
                  >
                    <Trash2 className="btn-icon text-red-500" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="user-info">
                <div className="user-role-badge">{user.role}</div>
                <div className="user-status">
                  <span className="status-label">Status:</span>
                  <Switch
                    checked={user.ativo}
                    onCheckedChange={() => handleToggleUserStatus(user.id, user.ativo)}
                    data-testid={`user-status-${user.id}`}
                  />
                  <span className={`status-text ${user.ativo ? 'active' : 'inactive'}`}>
                    {user.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                </div>
              </div>
              
              <div className="permissions-summary">
                <p className="summary-title">Permissões Ativas:</p>
                <div className="permissions-count">
                  {Object.values(user.permissoes || {}).filter(Boolean).length} de {Object.keys(permissionGroups).reduce((acc, key) => acc + permissionGroups[key].length, 0)}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default AdminUsers;
