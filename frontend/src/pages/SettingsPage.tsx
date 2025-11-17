// frontend/src/pages/SettingsPage.tsx
import React, { useState, useEffect } from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { apiService } from '../services/apiClient';
import type { AdoConnection, UserConfig, SystemModuleDetail } from '../types/models';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button'; 
import { Input } from '../components/ui/Input';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { Trash2, Plus, ExternalLink, Save, AlertCircle, CheckCircle2, Sun, Moon } from 'lucide-react';

type AdoFormInputs = {
  organization_url: string;
};

interface TabProps {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

const TABS: TabProps[] = [
  { id: 'profile', label: 'Perfil' },
  { id: 'modules', label: 'Módulos' },
  { id: 'ado', label: 'Azure DevOps' },
  { id: 'notifications', label: 'Notificações' },
  { id: 'theme', label: 'Tema' },
];

const SettingsPage: React.FC = () => {
    // State Global
    const [activeTab, setActiveTab] = useState('profile');
    
    // ADO
    const [connections, setConnections] = useState<AdoConnection[]>([]);
    const [adoLoading, setAdoLoading] = useState(true);
    const [adoError, setAdoError] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<number | null>(null);
    
    // Módulos
    const [systemModules, setSystemModules] = useState<SystemModuleDetail[]>([]);
    const [userConfig, setUserConfig] = useState<UserConfig | null>(null);
    const [modulesLoading, setModulesLoading] = useState(true);
    const [modulesSaved, setModulesSaved] = useState(false);
    
    // Notificações
    const [notifications, setNotifications] = useState({
      critical_alerts: true,
      skill_suggestions: true,
      meeting_reminders: true,
      ado_updates: true,
    });
    
    // Tema
    const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
    
    const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<AdoFormInputs>();

    // Carregar dados iniciais
    useEffect(() => {
        const loadData = async () => {
            try {
                const [modules, config, connections] = await Promise.all([
                    apiService.getSystemModules(),
                    apiService.getUserConfig(),
                    apiService.getAdoConnections(),
                ]);
                
                setSystemModules(modules);
                setUserConfig(config);
                setConnections(connections);
                setTheme((config.theme as 'light' | 'dark' | 'system') || 'system');
            } catch (err: any) {
                console.error('Erro ao carregar configurações:', err);
                setAdoError('Erro ao carregar configurações');
            } finally {
                setAdoLoading(false);
                setModulesLoading(false);
            }
        };
        
        loadData();
    }, []);

    // ========== ADO HANDLERS ==========
    const onAdoSubmit: SubmitHandler<AdoFormInputs> = async (data) => {
        setAdoError(null);
        try {
            const newConnection = await apiService.createAdoConnection(data.organization_url);
            setConnections(prev => [...prev, newConnection]);
            reset();
        } catch (err: any) {
            console.error(err);
            setAdoError(err.response?.data?.detail || "Erro ao salvar conexão. Verifique a URL ou se ela já existe.");
        }
    };

    const handleDeleteConnection = async (id: number) => {
        if (!window.confirm('Tem certeza que deseja remover esta conexão?')) return;
        
        setDeletingId(id);
        try {
            // TODO: Implementar endpoint DELETE /config/ado/connections/{id} no backend
            setConnections(prev => prev.filter(conn => conn.id !== id));
            setAdoError(null);
        } catch (err: any) {
            console.error(err);
            setAdoError('Erro ao deletar conexão');
        } finally {
            setDeletingId(null);
        }
    };

    // ========== MÓDULOS HANDLERS ==========
    const handleModuleToggle = (moduleId: string) => {
        if (!userConfig) return;
        
        const updatedModules = userConfig.modules.map(m =>
            m.module_id === moduleId ? { ...m, is_active: !m.is_active } : m
        );
        
        setUserConfig({ ...userConfig, modules: updatedModules });
    };

    const handleDragEnd = (result: DropResult) => {
        if (!userConfig || !result.destination) return;
        
        const items = Array.from(userConfig.modules);
        const [reorderedItem] = items.splice(result.source.index, 1);
        items.splice(result.destination.index, 0, reorderedItem);
        
        const updatedModules = items.map((item, index) => ({
            ...item,
            display_order: index + 1
        }));
        
        setUserConfig({ ...userConfig, modules: updatedModules });
    };

    const handleSaveModules = async () => {
        if (!userConfig) return;
        
        try {
            await apiService.updateUserModules(userConfig.modules);
            setModulesSaved(true);
            setTimeout(() => setModulesSaved(false), 3000);
        } catch (err: any) {
            console.error(err);
            setAdoError('Erro ao salvar preferências de módulos');
        }
    };

    // ========== TEMA HANDLER ==========
    const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
        setTheme(newTheme);
        if (newTheme === 'dark') {
            document.documentElement.classList.add('dark');
        } else if (newTheme === 'light') {
            document.documentElement.classList.remove('dark');
        }
    };

    // ========== RENDER TABS ==========
    const renderProfileTab = () => (
        <div className="space-y-6">
            <div className="bg-linear-to-r from-primary/10 to-accent/10 p-6 rounded-lg border border-primary/20">
                <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                        <div className="w-14 h-14 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-2xl font-bold">
                            👤
                        </div>
                    </div>
                    <div>
                        <p className="text-sm text-muted-foreground">Usuário autenticado</p>
                        <p className="text-lg font-semibold">FlowMaster User</p>
                        <p className="text-xs text-muted-foreground mt-1">Acesso desde {new Date().toLocaleDateString('pt-BR')}</p>
                    </div>
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="text-base">Informações da Conta</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <label className="text-sm font-medium">Email</label>
                        <p className="text-sm text-muted-foreground mt-1">usuario@example.com</p>
                    </div>
                    <div>
                        <label className="text-sm font-medium">Status</label>
                        <div className="flex items-center gap-2 mt-1">
                            <div className="w-2 h-2 rounded-full bg-green-500"></div>
                            <span className="text-sm text-green-600 dark:text-green-400">Ativo</span>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );

    const renderModulesTab = () => (
        <div className="space-y-6">
            {modulesLoading ? (
                <Card><CardContent className="p-6">Carregando módulos...</CardContent></Card>
            ) : userConfig ? (
                <>
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">Módulos Ativos</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground mb-4">
                                Arraste para reordenar. Os módulos desabilitados não aparecerão no dashboard.
                            </p>
                            
                            <DragDropContext onDragEnd={handleDragEnd}>
                                <Droppable droppableId="modules-list">
                                    {(provided) => (
                                        <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-2">
                                            {userConfig.modules.map((pref, index) => {
                                                const module = systemModules.find(m => m.id === pref.module_id);
                                                if (!module) return null;

                                                return (
                                                    <Draggable key={pref.module_id} draggableId={pref.module_id} index={index}>
                                                        {(provided, snapshot) => (
                                                            <div
                                                                ref={provided.innerRef}
                                                                {...provided.draggableProps}
                                                                {...provided.dragHandleProps}
                                                                className={`p-4 rounded-lg border transition-all ${
                                                                    snapshot.isDragging 
                                                                        ? 'bg-primary/10 border-primary shadow-lg' 
                                                                        : 'bg-background border-border hover:border-primary/50'
                                                                } ${!pref.is_active ? 'opacity-50' : ''}`}
                                                            >
                                                                <div className="flex items-center justify-between">
                                                                    <div className="flex-1 min-w-0">
                                                                        <h4 className="font-medium text-sm">{module.name}</h4>
                                                                        <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{module.description}</p>
                                                                    </div>
                                                                    <label className="flex items-center gap-2 ml-4 cursor-pointer">
                                                                        <input
                                                                            type="checkbox"
                                                                            checked={pref.is_active}
                                                                            onChange={() => handleModuleToggle(pref.module_id)}
                                                                            className="w-4 h-4 rounded border-gray-300 text-primary accent-primary"
                                                                        />
                                                                        <span className="text-xs font-medium">{pref.is_active ? 'Ativo' : 'Inativo'}</span>
                                                                    </label>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </Draggable>
                                                );
                                            })}
                                            {provided.placeholder}
                                        </div>
                                    )}
                                </Droppable>
                            </DragDropContext>

                            <div className="mt-6 flex gap-2">
                                <Button onClick={handleSaveModules} className="gap-2">
                                    <Save className="w-4 h-4" />
                                    Salvar Configurações
                                </Button>
                                {modulesSaved && (
                                    <div className="flex items-center gap-2 text-green-600 dark:text-green-400 text-sm">
                                        <CheckCircle2 className="w-4 h-4" />
                                        Salvo com sucesso!
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </>
            ) : null}
        </div>
    );

    const renderAdoTab = () => (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="text-base">Adicionar Conexão</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                        Adicione as URLs das Organizações do Azure DevOps que você deseja monitorar.
                    </p>
                    
                    <form onSubmit={handleSubmit(onAdoSubmit)} className="flex gap-2 mb-4">
                        <Input 
                            {...register("organization_url", { required: true })}
                            placeholder="https://dev.azure.com/sua-organizacao"
                            className="flex-1"
                            type="url"
                        />
                        <Button type="submit" disabled={isSubmitting} className="gap-2">
                            <Plus className="w-4 h-4" />
                            {isSubmitting ? "Adicionando..." : "Adicionar"}
                        </Button>
                    </form>
                    
                    {adoError && (
                        <div className="flex gap-2 items-start p-3 rounded-lg bg-destructive/10 border border-destructive/30 mb-4">
                            <AlertCircle className="w-4 h-4 text-destructive mt-0.5 shrink-0" />
                            <p className="text-sm text-destructive">{adoError}</p>
                        </div>
                    )}
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle className="text-base">Conexões Ativas</CardTitle>
                </CardHeader>
                <CardContent>
                    {adoLoading ? (
                        <p className="text-sm text-muted-foreground">Carregando conexões...</p>
                    ) : connections.length === 0 ? (
                        <p className="text-sm text-muted-foreground">Nenhuma conexão configurada ainda.</p>
                    ) : (
                        <div className="space-y-2">
                            {connections.map(conn => (
                                <div 
                                    key={conn.id} 
                                    className="flex items-center justify-between p-3 rounded-lg border border-border hover:border-primary/50 transition-colors"
                                >
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{conn.organization_url}</p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {conn.is_active ? '🟢 Ativa' : '🔴 Inativa'}
                                        </p>
                                    </div>
                                    <div className="flex gap-2 ml-4">
                                        <Button 
                                            variant="ghost" 
                                            size="icon"
                                            onClick={() => window.open(conn.organization_url, '_blank')}
                                            title="Abrir no Azure DevOps"
                                            className="h-8 w-8"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                        </Button>
                                        <Button 
                                            variant="ghost" 
                                            size="icon"
                                            onClick={() => handleDeleteConnection(conn.id)}
                                            disabled={deletingId === conn.id}
                                            title="Remover conexão"
                                            className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                                        >
                                            {deletingId === conn.id ? (
                                                <div className="w-4 h-4 border-2 border-destructive border-t-transparent rounded-full animate-spin"></div>
                                            ) : (
                                                <Trash2 className="w-4 h-4" />
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );

    const renderNotificationsTab = () => (
        <Card>
            <CardHeader>
                <CardTitle className="text-base">Preferências de Notificações</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground mb-4">
                    Controle quais notificações você deseja receber.
                </p>

                {Object.entries(notifications).map(([key, value]) => (
                    <label key={key} className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-primary/50 cursor-pointer transition-colors">
                        <input
                            type="checkbox"
                            checked={value}
                            onChange={(e) => setNotifications({ ...notifications, [key]: e.target.checked })}
                            className="w-4 h-4 rounded border-gray-300 text-primary accent-primary"
                        />
                        <div className="flex-1">
                            <p className="text-sm font-medium">
                                {key === 'critical_alerts' && 'Alertas Críticos'}
                                {key === 'skill_suggestions' && 'Sugestões de Skills'}
                                {key === 'meeting_reminders' && 'Lembretes de Reuniões'}
                                {key === 'ado_updates' && 'Atualizações do Azure DevOps'}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                {key === 'critical_alerts' && 'Receba notificações de problemas críticos detectados'}
                                {key === 'skill_suggestions' && 'Receba sugestões de cursos e conhecimentos relevantes'}
                                {key === 'meeting_reminders' && 'Receba lembretes de reuniões sugeridas'}
                                {key === 'ado_updates' && 'Receba atualizações dos seus projetos no Azure DevOps'}
                            </p>
                        </div>
                    </label>
                ))}

                <Button className="w-full mt-6">Salvar Preferências</Button>
            </CardContent>
        </Card>
    );

    const renderThemeTab = () => (
        <Card>
            <CardHeader>
                <CardTitle className="text-base">Preferência de Tema</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground mb-4">
                    Escolha como você deseja que o FlowMaster seja exibido.
                </p>

                <div className="grid grid-cols-3 gap-4">
                    {(['light', 'dark', 'system'] as const).map((t) => (
                        <button
                            key={t}
                            onClick={() => handleThemeChange(t)}
                            className={`p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2 ${
                                theme === t
                                    ? 'border-primary bg-primary/10'
                                    : 'border-border hover:border-primary/50'
                            }`}
                        >
                            {t === 'light' && <Sun className="w-6 h-6 text-yellow-500" />}
                            {t === 'dark' && <Moon className="w-6 h-6 text-slate-600" />}
                            {t === 'system' && <div className="w-6 h-6 flex items-center gap-1"><Sun className="w-3 h-3 text-yellow-500" /><Moon className="w-3 h-3 text-slate-600" /></div>}
                            <span className="text-sm font-medium capitalize">
                                {t === 'light' && 'Claro'}
                                {t === 'dark' && 'Escuro'}
                                {t === 'system' && 'Sistema'}
                            </span>
                        </button>
                    ))}
                </div>
            </CardContent>
        </Card>
    );

    return (
        <main className="min-h-screen bg-linear-to-br from-background to-muted/30">
            <div className="max-w-4xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold tracking-tight">Configurações</h1>
                    <p className="text-muted-foreground mt-2">Personalize sua experiência no FlowMaster AI</p>
                </div>

                {/* Tabs Navigation */}
                <div className="flex gap-1 mb-8 bg-muted/50 p-1 rounded-lg border border-border flex-wrap">
                    {TABS.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex-1 min-w-max px-4 py-2 rounded-md transition-all text-sm font-medium ${
                                activeTab === tab.id
                                    ? 'bg-primary text-primary-foreground shadow-sm'
                                    : 'text-foreground hover:bg-background/50'
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="animate-in fade-in duration-200">
                    {activeTab === 'profile' && renderProfileTab()}
                    {activeTab === 'modules' && renderModulesTab()}
                    {activeTab === 'ado' && renderAdoTab()}
                    {activeTab === 'notifications' && renderNotificationsTab()}
                    {activeTab === 'theme' && renderThemeTab()}
                </div>
            </div>
        </main>
    );
};

export default SettingsPage;