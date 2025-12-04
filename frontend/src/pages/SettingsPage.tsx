// frontend/src/pages/SettingsPage.tsx

import React, { useState, useEffect } from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { apiService } from '../services/apiClient';
import type { AdoConnection, UserConfig, SystemModuleDetail } from '../types/models';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button'; 
import { Input } from '../components/ui/Input';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { Trash2, Plus, ExternalLink, Save, AlertCircle, CheckCircle2, Sun, Moon, ArrowLeft, Edit2, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

type AdoFormInputs = {
  organization_url: string;
  personal_access_token?: string;
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
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('profile');
    
    // ADO States
    const [connections, setConnections] = useState<AdoConnection[]>([]);
    const [adoLoading, setAdoLoading] = useState(true);
    const [adoError, setAdoError] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<number | null>(null);
    
    // ✅ Novos States para Edição
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editPat, setEditPat] = useState("");
    const [savingEdit, setSavingEdit] = useState(false);
    
    // Outros States
    const [systemModules, setSystemModules] = useState<SystemModuleDetail[]>([]);
    const [userConfig, setUserConfig] = useState<UserConfig | null>(null);
    const [modulesLoading, setModulesLoading] = useState(true);
    const [modulesSaved, setModulesSaved] = useState(false);
    const [configSaved, setConfigSaved] = useState(false);
    const [notifications, setNotifications] = useState({
      critical_alerts: true,
      skill_suggestions: true,
      meeting_reminders: true,
      ado_updates: true,
    });
    const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
    
    const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<AdoFormInputs>();

    useEffect(() => {
        const loadData = async () => {
            try {
                const [modules, config, connectionsData] = await Promise.all([
                    apiService.getSystemModules(),
                    apiService.getUserConfig(),
                    apiService.getAdoConnections(),
                ]);
                setSystemModules(modules);
                setUserConfig(config);
                setConnections(connectionsData);
                setTheme((config.theme as 'light' | 'dark' | 'system') || 'system');
            } catch (err: any) {
                console.error(err);
                setAdoError('Erro ao carregar configurações.');
            } finally {
                setAdoLoading(false);
                setModulesLoading(false);
            }
        };
        loadData();
    }, []);

    // --- Handlers ADO ---

    const onAdoSubmit: SubmitHandler<AdoFormInputs> = async (data) => {
        setAdoError(null);
        try {
            const newConnection = await apiService.createAdoConnection(data.organization_url, data.personal_access_token);
            // Se já existir (update), substitui no array, senão adiciona
            setConnections(prev => {
                const exists = prev.find(c => c.id === newConnection.id);
                if (exists) return prev.map(c => c.id === newConnection.id ? newConnection : c);
                return [...prev, newConnection];
            });
            reset();
        } catch (err: any) {
            setAdoError(err.response?.data?.detail || "Erro ao salvar conexão.");
        }
    };

    const handleDeleteConnection = async (id: number) => {
        if (!window.confirm('Remover esta conexão?')) return;
        setDeletingId(id);
        try {
            await apiService.deleteAdoConnection(id);
            setConnections(prev => prev.filter(conn => conn.id !== id));
        } catch (err: any) {
            setAdoError('Erro ao deletar conexão');
        } finally {
            setDeletingId(null);
        }
    };

    const startEditing = (id: number) => {
        setEditingId(id);
        setEditPat("");
        setAdoError(null);
    };

    const cancelEditing = () => {
        setEditingId(null);
        setEditPat("");
    };

    const handleUpdateConnection = async (id: number) => {
        if (!editPat) {
            setAdoError("Insira um token válido.");
            return;
        }
        setSavingEdit(true);
        try {
            const updated = await apiService.updateAdoConnectionPat(id, editPat);
            setConnections(prev => prev.map(c => c.id === id ? updated : c));
            setEditingId(null);
            setEditPat("");
        } catch (err: any) {
            setAdoError("Erro ao atualizar token.");
        } finally {
            setSavingEdit(false);
        }
    };

    // --- Handlers Módulos/Geral --- (Mantidos iguais)
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
        } catch (err) { setAdoError('Erro ao salvar módulos'); }
    };

    const handleSaveNotifications = async () => {
        try {
             // @ts-ignore
            if (apiService.updateUserConfig) await apiService.updateUserConfig({ notifications });
            setConfigSaved(true);
            setTimeout(() => setConfigSaved(false), 3000);
        } catch (err) { console.error(err); }
    };

    const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
        setTheme(newTheme);
        if (newTheme === 'dark') document.documentElement.classList.add('dark');
        else if (newTheme === 'light') document.documentElement.classList.remove('dark');
    };

    // --- Renders ---

    const renderProfileTab = () => (
        <div className="space-y-6">
            <Card>
                <CardHeader><CardTitle>Perfil</CardTitle></CardHeader>
                <CardContent>
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-2xl">👤</div>
                        <div>
                            <p className="font-medium">Usuário FlowMaster</p>
                            <p className="text-sm text-muted-foreground">usuario@exemplo.com</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );

    const renderModulesTab = () => (
        <div className="space-y-6">
            {modulesLoading ? <p>Carregando...</p> : userConfig && (
                <Card>
                    <CardHeader><CardTitle>Módulos</CardTitle></CardHeader>
                    <CardContent>
                        <DragDropContext onDragEnd={handleDragEnd}>
                            <Droppable droppableId="modules">
                                {(provided) => (
                                    <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-2">
                                        {userConfig.modules.map((pref, idx) => {
                                            const mod = systemModules.find(m => m.id === pref.module_id);
                                            if (!mod) return null;
                                            return (
                                                <Draggable key={pref.module_id} draggableId={pref.module_id} index={idx}>
                                                    {(provided) => (
                                                        <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} className="p-3 border rounded flex justify-between bg-card">
                                                            <span>{mod.name}</span>
                                                            <input type="checkbox" checked={pref.is_active} onChange={() => handleModuleToggle(pref.module_id)} />
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
                        <Button className="mt-4" onClick={handleSaveModules}>Salvar</Button>
                        {modulesSaved && <span className="text-green-500 ml-2">Salvo!</span>}
                    </CardContent>
                </Card>
            )}
        </div>
    );

    const renderAdoTab = () => (
        <div className="space-y-6">
            <Card>
                <CardHeader><CardTitle className="text-base">Adicionar Conexão</CardTitle></CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                        URL da Organização e PAT (Opcional).
                    </p>
                    <form onSubmit={handleSubmit(onAdoSubmit)} className="space-y-3">
                        <div className="grid gap-2">
                            <Input {...register("organization_url", { required: true })} placeholder="https://dev.azure.com/org" />
                        </div>
                        <div className="grid gap-2">
                            <Input {...register("personal_access_token")} type="password" placeholder="PAT (Opcional)" />
                        </div>
                        <Button type="submit" disabled={isSubmitting}><Plus className="w-4 h-4 mr-2" /> Salvar</Button>
                    </form>
                    {adoError && <p className="text-sm text-red-500 mt-2">{adoError}</p>}
                </CardContent>
            </Card>
            
            <Card>
                <CardHeader><CardTitle className="text-base">Conexões Ativas</CardTitle></CardHeader>
                <CardContent>
                    {adoLoading ? <p>Carregando...</p> : connections.length === 0 ? <p className="text-muted-foreground">Nenhuma.</p> : (
                        <div className="space-y-3">
                            {connections.map(conn => (
                                <div key={conn.id} className="p-3 border rounded-lg flex flex-col gap-2 bg-card">
                                    <div className="flex justify-between items-start">
                                        <div className="min-w-0">
                                            <p className="font-medium truncate text-sm">{conn.organization_url}</p>
                                            <div className="flex gap-2 mt-1">
                                                <span className="text-xs text-muted-foreground">{conn.is_active ? 'Ativa' : 'Inativa'}</span>
                                                {/* @ts-ignore */}
                                                {conn.has_pat && <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">PAT</span>}
                                            </div>
                                        </div>
                                        <div className="flex gap-1">
                                            <Button variant="ghost" size="icon" onClick={() => window.open(conn.organization_url, '_blank')}><ExternalLink className="w-4 h-4" /></Button>
                                            <Button variant="ghost" size="icon" onClick={() => handleDeleteConnection(conn.id)}><Trash2 className="w-4 h-4 text-red-500" /></Button>
                                            <Button variant="ghost" size="icon" onClick={() => startEditing(conn.id)}><Edit2 className="w-4 h-4" /></Button>
                                        </div>
                                    </div>
                                    
                                    {/* Modo Edição Inline */}
                                    {editingId === conn.id && (
                                        <div className="mt-2 p-2 bg-muted/50 rounded animate-in fade-in slide-in-from-top-1">
                                            <p className="text-xs font-medium mb-1">Atualizar Token (PAT)</p>
                                            <div className="flex gap-2">
                                                <Input 
                                                    type="password" 
                                                    value={editPat} 
                                                    onChange={(e) => setEditPat(e.target.value)} 
                                                    placeholder="Novo PAT..." 
                                                    className="h-8 text-sm"
                                                />
                                                <Button size="sm" onClick={() => handleUpdateConnection(conn.id)} disabled={savingEdit}>
                                                    {savingEdit ? '...' : <Save className="w-3 h-3" />}
                                                </Button>
                                                <Button size="sm" variant="ghost" onClick={cancelEditing}>
                                                    <X className="w-3 h-3" />
                                                </Button>
                                            </div>
                                        </div>
                                    )}
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
            <CardHeader><CardTitle>Notificações</CardTitle></CardHeader>
            <CardContent>
                <div className="space-y-2">
                    {Object.entries(notifications).map(([k, v]) => (
                        <label key={k} className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={v} onChange={e => setNotifications({...notifications, [k]: e.target.checked})} />
                            <span className="capitalize">{k.replace('_', ' ')}</span>
                        </label>
                    ))}
                    <Button onClick={handleSaveNotifications} className="mt-4">Salvar</Button>
                    {configSaved && <span className="ml-2 text-green-500">Salvo!</span>}
                </div>
            </CardContent>
        </Card>
    );

    const renderThemeTab = () => (
        <Card>
            <CardHeader><CardTitle>Tema</CardTitle></CardHeader>
            <CardContent>
                <div className="flex gap-2">
                    {['light', 'dark', 'system'].map((t: any) => (
                        <Button key={t} variant={theme === t ? "default" : "outline"} onClick={() => handleThemeChange(t)} className="capitalize">
                            {t === 'light' && <Sun className="w-4 h-4 mr-2" />}
                            {t === 'dark' && <Moon className="w-4 h-4 mr-2" />}
                            {t}
                        </Button>
                    ))}
                </div>
            </CardContent>
        </Card>
    );

    return (
        <main className="min-h-screen bg-background p-4 md:p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <Button variant="ghost" size="icon" onClick={() => navigate('/')}><ArrowLeft className="w-6 h-6" /></Button>
                    <h1 className="text-3xl font-bold">Configurações</h1>
                </div>

                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {TABS.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
                                activeTab === tab.id ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80 text-muted-foreground'
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {activeTab === 'profile' && renderProfileTab()}
                {activeTab === 'modules' && renderModulesTab()}
                {activeTab === 'ado' && renderAdoTab()}
                {activeTab === 'notifications' && renderNotificationsTab()}
                {activeTab === 'theme' && renderThemeTab()}
            </div>
        </main>
    );
};

export default SettingsPage;