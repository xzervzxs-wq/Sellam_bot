// Data Management Helper
// ملف مساعد لإدارة البيانات المحلية

class LocalDataManager {
    constructor() {
        this.dataPath = './data/';
    }

    // Load data from JSON file
    async loadFromFile(filename) {
        try {
            const response = await fetch(`${this.dataPath}${filename}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error loading ${filename}:`, error);
            return this.getDefaultData(filename);
        }
    }

    // Save data to localStorage (fallback for browser environment)
    saveToStorage(filename, data) {
        try {
            const key = `local_${filename.replace('.json', '')}`;
            localStorage.setItem(key, JSON.stringify(data));
            console.log(`✓ Data saved locally: ${filename}`);
            this.updateLastSaved(filename);
            return true;
        } catch (error) {
            console.error(`Error saving ${filename}:`, error);
            return false;
        }
    }

    // Update last saved timestamp
    updateLastSaved(filename) {
        const timestamp = new Date().toISOString();
        localStorage.setItem('lastSaved', timestamp);
        localStorage.setItem(`lastSaved_${filename}`, timestamp);
    }

    // Get default data for each file type
    getDefaultData(filename) {
        const defaults = {
            'screens.json': this.generateDefaultScreens(),
            'users.json': this.generateDefaultUsers(),
            'external_departments.json': [],
            'policies.json': [],
            'activity_log.json': [],
            'incidents.json': [],
            'maintenance.json': [],
            'settings.json': this.generateDefaultSettings()
        };
        return defaults[filename] || [];
    }

    // Generate default screens data
    generateDefaultScreens() {
        return Array.from({ length: 12 }, (_, i) => ({
            id: i + 1,
            charId: String.fromCharCode(65 + i), // A, B, C, etc.
            name: `شاشة العرض ${i + 1}`,
            status: 'active',
            statusReason: '',
            cameras: Array.from({ length: 10 }, (_, j) => ({
                id: `${i + 1}-${j + 1}`,
                number: j + 1,
                name: `كاميرا ${j + 1}`,
                code: `CAM-${i + 1}-${j + 1}`,
                status: Math.random() > 0.1 ? 'active' : 'maintenance', // 90% active
                note: '',
                lastUpdate: '10:00',
                location: '',
                storage: {
                    dailyHours: '24',
                    retentionDays: '30'
                },
                incidents: [],
                inspections: [],
                recordings: [],
                maintenance: []
            }))
        }));
    }

    // Generate default users
    generateDefaultUsers() {
        return [
            { id: 1, name: 'Admin', code: '1234', role: 'admin' },
            { id: 2, name: 'محمد الأحمد', code: '5678', role: 'viewer' },
            { id: 3, name: 'سارة المطيري', code: '9012', role: 'viewer' }
        ];
    }

    // Generate default settings
    generateDefaultSettings() {
        return {
            systemName: 'نظام المراقبة المحلي',
            version: '2.1.0',
            lastBackup: null,
            backupEnabled: true,
            autoSave: true,
            theme: 'dark',
            language: 'ar',
            timezone: 'Asia/Riyadh',
            enableNotifications: true,
            enableSounds: false,
            maxLogEntries: 500
        };
    }

    // Export all data as single file
    async exportAllData() {
        try {
            const allData = {
                users: await this.loadFromFile('users.json'),
                screens: await this.loadFromFile('screens.json'),
                externalDepartments: await this.loadFromFile('external_departments.json'),
                policies: await this.loadFromFile('policies.json'),
                activityLog: await this.loadFromFile('activity_log.json'),
                incidents: await this.loadFromFile('incidents.json'),
                maintenance: await this.loadFromFile('maintenance.json'),
                settings: await this.loadFromFile('settings.json'),
                exportInfo: {
                    date: new Date().toISOString(),
                    version: '2.1.0',
                    type: 'full_backup'
                }
            };

            const blob = new Blob([JSON.stringify(allData, null, 2)], { 
                type: 'application/json' 
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `security_backup_${new Date().toISOString().slice(0, 10)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            return true;
        } catch (error) {
            console.error('Export failed:', error);
            return false;
        }
    }

    // Import data from file
    async importData(file) {
        try {
            const text = await file.text();
            const data = JSON.parse(text);

            // Validate structure
            if (!this.validateImportData(data)) {
                throw new Error('Invalid data structure');
            }

            // Save each data type
            const promises = [];
            if (data.users) promises.push(this.saveToStorage('users.json', data.users));
            if (data.screens) promises.push(this.saveToStorage('screens.json', data.screens));
            if (data.externalDepartments) promises.push(this.saveToStorage('external_departments.json', data.externalDepartments));
            if (data.policies) promises.push(this.saveToStorage('policies.json', data.policies));
            if (data.activityLog) promises.push(this.saveToStorage('activity_log.json', data.activityLog));
            if (data.incidents) promises.push(this.saveToStorage('incidents.json', data.incidents));
            if (data.maintenance) promises.push(this.saveToStorage('maintenance.json', data.maintenance));
            if (data.settings) promises.push(this.saveToStorage('settings.json', data.settings));

            await Promise.all(promises);
            return true;
        } catch (error) {
            console.error('Import failed:', error);
            return false;
        }
    }

    // Validate imported data structure
    validateImportData(data) {
        const requiredFields = ['users', 'screens'];
        return requiredFields.every(field => data[field] && Array.isArray(data[field]));
    }

    // Generate sample incident data
    generateSampleIncident() {
        return {
            id: Date.now(),
            type: 'security',
            severity: 'medium',
            title: 'حادثة تجريبية',
            description: 'وصف الحادثة...',
            location: 'المنطقة الشمالية',
            reportedBy: 'النظام',
            status: 'open',
            createdAt: new Date().toISOString()
        };
    }

    // Generate sample maintenance record
    generateSampleMaintenance() {
        return {
            id: Date.now(),
            type: 'routine',
            title: 'صيانة دورية',
            description: 'فحص دوري للكاميرات',
            scheduledDate: new Date().toISOString().split('T')[0],
            status: 'pending',
            assignedTo: 'فريق الصيانة',
            createdAt: new Date().toISOString()
        };
    }
}

// Global data manager instance
window.dataManager = new LocalDataManager();

// Utility functions for data operations
window.dataUtils = {
    // Format date for Arabic display
    formatDate: (dateString) => {
        return new Date(dateString).toLocaleDateString('ar-SA', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },

    // Format time for Arabic display
    formatTime: (dateString) => {
        return new Date(dateString).toLocaleTimeString('ar-SA', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Generate unique ID
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    // Validate Arabic phone number
    validatePhone: (phone) => {
        const regex = /^(05|5)[0-9]{8}$/;
        return regex.test(phone.replace(/\s+/g, ''));
    },

    // Validate access code
    validateAccessCode: (code) => {
        // Normalize Arabic and Persian digits
        return code.replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d))
                  .replace(/[۰-۹]/g, d => "۰۱۲۳۴۵۶۷۸۹".indexOf(d));
    }
};

console.log('📁 محول البيانات المحلي جاهز للاستخدام');