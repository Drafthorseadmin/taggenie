import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  Chip,
  Grid,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
} from '@mui/material';
import axios from 'axios';
import { translations } from './translations';
import logo from './assets/logo.png';

const steps = ['describe', 'review', 'save'];

function App() {
  const [activeStep, setActiveStep] = useState(0);
  const [description, setDescription] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTags, setSelectedTags] = useState([]);
  const [isFallback, setIsFallback] = useState(false);
  const [error, setError] = useState(null);
  const [uiLanguage, setUiLanguage] = useState('fi');
  const [conditionalTags, setConditionalTags] = useState([]);
  const [tagType, setTagType] = useState('template'); // 'template' or 'asset'
  // const [inputMethod, setInputMethod] = useState('description'); // 'description' or 'filename'

  const t = translations[uiLanguage];

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleStartNew = () => {
    setDescription('');
    setSuggestions([]);
    setSelectedTags([]);
    setIsFallback(false);
    setError(null);
    setActiveStep(0);
    setConditionalTags([]);
  };

  const handleGetSuggestions = async () => {
    setLoading(true);
    setError(null);
    setSuggestions([]);
    setSelectedTags([]);
    setConditionalTags([]);

    try {
      const response = await axios.post('/api/suggest_tags', {
        description: description,
        type: tagType
      });
      setSuggestions(response.data.suggestions);
      setIsFallback(response.data.is_fallback || false);
      if (response.data.error) {
        setError(response.data.error);
      }
      setActiveStep(1);
    } catch (error) {
      console.error('Error getting suggestions:', error);
      setError(error.response?.data?.error || error.message);
      setActiveStep(1);
    } finally {
      setLoading(false);
    }
  };

  const handleTagSelect = (tag) => {
    setSelectedTags((prev) => {
      const newTags = prev.includes(tag) 
        ? prev.filter((t) => t !== tag)
        : [...prev, tag];
      
      // Check for conditional tags
      const newConditionalTags = [];
      suggestions.forEach(suggestion => {
        if (suggestion.conditional_tags) {
          Object.entries(suggestion.conditional_tags).forEach(([conditionalTag, config]) => {
            if (config.trigger_tags.some(triggerTag => newTags.includes(triggerTag))) {
              newConditionalTags.push({
                tag: conditionalTag,
                description: config.description[uiLanguage] || config.description['en']
              });
            }
          });
        }
      });
      setConditionalTags(newConditionalTags);
      
      return newTags;
    });
  };

  const generateFilename = () => {
    if (selectedTags.length === 0) return 'tags.txt';
    
    const language = selectedTags.find(tag => tag.startsWith('language/'))?.split('/')[1] || '';
    const vehicle = selectedTags.find(tag => tag.startsWith('filter/'))?.split('/').pop() || '';
    const media = selectedTags.find(tag => tag.startsWith('system/media/'))?.split('/')[2] || '';
    const size = selectedTags.find(tag => tag.startsWith('system/size/'))?.split('/')[2] || '';
    const assetType = selectedTags.find(tag => tag.startsWith('type/'))?.split('/')[1] || '';
    
    const parts = [];
    
    // For asset tags, use a different naming pattern
    if (tagType === 'asset') {
      if (language) parts.push(language);
      if (assetType) parts.push(assetType);
      if (vehicle) parts.push(vehicle);
      return parts.length > 0 ? `${parts.join('_')}_asset_tags.txt` : 'asset_tags.txt';
    }
    
    // For template tags, use the existing pattern
    if (language) parts.push(language);
    if (vehicle) parts.push(vehicle);
    if (media) parts.push(media);
    if (size) parts.push(size);
    
    return parts.length > 0 ? `${parts.join('_')}_tags.txt` : 'tags.txt';
  };

  const handleSaveTags = () => {
    const content = selectedTags.join('\n');
    const filename = generateFilename();
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>{t.type.label}</InputLabel>
              <Select
                value={tagType}
                label={t.type.label}
                onChange={(e) => setTagType(e.target.value)}
              >
                <MenuItem value="template">{t.type.options.template}</MenuItem>
                <MenuItem value="asset">{t.type.options.asset}</MenuItem>
              </Select>
            </FormControl>
            
            {/* <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>{t.inputMethod.label}</InputLabel>
              <Select
                value={inputMethod}
                label={t.inputMethod.label}
                onChange={(e) => setInputMethod(e.target.value)}
              >
                <MenuItem value="description">{t.inputMethod.options.description}</MenuItem>
                <MenuItem value="filename">{t.inputMethod.options.filename}</MenuItem>
              </Select>
            </FormControl> */}

            <TextField
              fullWidth
              multiline
              rows={4}
              variant="outlined"
              label={t.description.label}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              sx={{ mb: 2 }}
            />
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleGetSuggestions}
              disabled={!description || loading}
              fullWidth
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : t.description.button}
            </Button>
          </Box>
        );
      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error.message}
              </Alert>
            )}
            {isFallback && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {t.suggestions.fallback} {error?.message}
              </Alert>
            )}
            <Typography variant="h6" gutterBottom>
              {t.suggestions.title}
            </Typography>
            <Grid container spacing={2}>
              {suggestions.map((suggestion, index) => (
                <Grid item xs={12} key={index}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      {suggestion.category}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {suggestion.suggested_tags.map((tag, tagIndex) => (
                        <Chip
                          key={tagIndex}
                          label={tag}
                          onClick={() => handleTagSelect(tag)}
                          color={selectedTags.includes(tag) ? "primary" : "default"}
                          sx={{ m: 0.5 }}
                        />
                      ))}
                    </Box>
                    {suggestion.category === 'banner/size' && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {t.suggestions.bannerSize}
                      </Typography>
                    )}
                  </Paper>
                </Grid>
              ))}
              {conditionalTags.length > 0 && (
                <Grid item xs={12}>
                  <Paper sx={{ p: 2, bgcolor: 'info.light' }}>
                    <Typography variant="subtitle1" gutterBottom>
                      {t.suggestions.conditional}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {conditionalTags.map(({ tag, description }) => (
                        <Chip
                          key={tag}
                          label={tag}
                          onClick={() => handleTagSelect(tag)}
                          color={selectedTags.includes(tag) ? 'primary' : 'default'}
                          title={description}
                        />
                      ))}
                    </Box>
                  </Paper>
                </Grid>
              )}
            </Grid>
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'flex-end', 
              mt: 2,
              gap: 1,
              flexDirection: { xs: 'column', sm: 'row' }
            }}>
              <Button onClick={handleBack} fullWidth={window.innerWidth < 600}>
                {t.buttons.back}
              </Button>
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={selectedTags.length === 0}
                fullWidth={window.innerWidth < 600}
              >
                {t.buttons.next}
              </Button>
            </Box>
          </Box>
        );
      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              {t.selected.title}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {selectedTags.map((tag) => (
                <Chip key={tag} label={tag} color="primary" />
              ))}
            </Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t.selected.saveAs} {generateFilename()}
            </Typography>
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'flex-end',
              gap: 1,
              flexDirection: { xs: 'column', sm: 'row' }
            }}>
              <Button onClick={handleStartNew} fullWidth={window.innerWidth < 600}>
                {t.buttons.startNew}
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={handleSaveTags}
                fullWidth={window.innerWidth < 600}
              >
                {t.buttons.saveTags}
              </Button>
            </Box>
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: { xs: 2, sm: 4 }, px: { xs: 1, sm: 2 } }}>
      <Paper sx={{ p: { xs: 2, sm: 4 } }}>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between', 
          alignItems: { xs: 'flex-start', sm: 'center' }, 
          gap: 2,
          mb: 4 
        }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 2,
            flexWrap: 'wrap'
          }}>
            <img src={logo} alt="Drafthorse Logo" style={{ height: '40px' }} />
            <Typography variant="h4" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>
              {t.title}
            </Typography>
          </Box>
          <FormControl sx={{ minWidth: 120, width: { xs: '100%', sm: 'auto' } }}>
            <InputLabel>{t.language.label}</InputLabel>
            <Select
              value={uiLanguage}
              label={t.language.label}
              onChange={(e) => setUiLanguage(e.target.value)}
            >
              {Object.entries(t.language.options).map(([code, name]) => (
                <MenuItem key={code} value={code}>
                  {name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        <Stepper activeStep={activeStep} sx={{ mb: 4, overflowX: 'auto' }}>
          {steps.map((step) => (
            <Step key={step}>
              <StepLabel>{t.steps[step]}</StepLabel>
            </Step>
          ))}
        </Stepper>
        {renderStepContent(activeStep)}
      </Paper>
    </Container>
  );
}

export default App; 